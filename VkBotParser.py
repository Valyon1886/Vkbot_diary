import sys
from contextlib import suppress
from datetime import time, datetime
from hashlib import md5
from re import search, findall, sub
from time import sleep
from traceback import print_exception

from dateparser import parse as date_parse
from bs4 import BeautifulSoup
from colorama import Fore, Style
from peewee import fn, DoesNotExist
from requests import get
from xlrd import open_workbook
from xlrd.sheet import Sheet

from InitConfig import Config
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days, Subjects, Lesson_start_end, Groups, ExamDays, Disciplines


class Parser:
    """Класс Parser используется для получения расписания с сайта МИРЭА."""
    _week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    _lesson_times_parsed_for_table = False
    _schedule_info = None
    _bot_parsing = False
    _parsed_date: datetime
    _parsed_percent: float

    @staticmethod
    def get_bot_parsing_state() -> bool:
        """Возвращает значение парсит ли бот расписание или нет

        Return
        ----------
        bot_parsing: bool
            парсит ли бот расписание
        """
        return Parser._bot_parsing

    @staticmethod
    def set_bot_parsed_date(last_parsed_date: datetime) -> None:
        """Устанавливает последнюю дату парсинга/начала парсинга

        Parameters
        ----------
        last_parsed_date: datetime
            дата последнего парсинга
        """
        Parser._parsed_date = last_parsed_date

    @staticmethod
    def get_bot_parsed_date() -> datetime:
        """Возвращает последнюю дату парсинга/начала парсинга

        Return
        ----------
        last_parsed_date: datetime
            дата последнего парсинга
        """
        return Parser._parsed_date

    @staticmethod
    def get_bot_parsed_percent() -> float:
        """Возвращает процент парсинга

        Return
        ----------
        parsed_percent: float
            процент парсинга
        """
        return Parser._parsed_percent

    @staticmethod
    def download_schedules() -> bool:
        """Скачивает актуальное расписание с сайта МИРЭА

        Return
        ----------
        all_files_parsed: bool
            пропарсены все ли файлы
        """
        Parser._bot_parsing = True
        last_parsed_date = Parser._parsed_date
        Parser._parsed_date = datetime.now()
        Parser._parsed_percent = 0.0
        files_parsed = []
        hashed_files = 0
        result_links = []
        parse_all_files_anyway = False
        number_of_tries = 3
        if Parser._schedule_info is None:
            Parser._schedule_info = Config.get_schedule_info()
        try:
            # Parsing html page for links
            page = get("https://www.mirea.ru/schedule/")
            soup = BeautifulSoup(page.text, "html.parser")
            uni_names = soup.find("div", {"class": "schedule"}).find_all("a", {"class": "uk-text-bold"})
            uni_names = list(set([sub(r"\n\s{2,}", " ", i.contents[0]) for i in uni_names]))
            with suppress(ValueError):
                uni_names.remove("Филиал в городе Ставрополе")
            for name in uni_names:
                links = []
                nav_links = soup.find("div", {"class": "schedule"}).findAll(string=name)
                for link in nav_links:
                    links.extend(
                        link.find_parent("div").find_parent("div").findAll("a", {"class": "uk-link-toggle"})
                    )
                links = [link["href"] for link in links]
                if len(links) > 0:
                    result_links.extend(links)
        except BaseException as ex:
            print(Fore.LIGHTRED_EX +
                  "Ошибка: Что-то пошло не так с нахождением институтов. Опять серваки МИРЭА падают?)"
                  + Style.RESET_ALL)
            print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)
            return False

        tables_length = [
            len([i for i in Groups.select().limit(1).execute()]),
        ]

        if any([i == 0 for i in tables_length]) and not all([i == 0 for i in tables_length]) or \
                Config.get_drop_schedule_tables():
            if Config.get_drop_schedule_tables():
                print(Fore.LIGHTRED_EX +
                      "Очищаем таблицы с расписанием по требованию пользователя!" + Style.RESET_ALL)
            else:
                print(Fore.LIGHTRED_EX +
                      "Одна из таблиц с расписанием оказалась пуста! Заполняем все снова!" +
                      Style.RESET_ALL)
            parse_all_files_anyway = True
            InitSQL.get_DB().drop_tables([Groups, Weeks, Days, Subjects, ExamDays, Disciplines, Lesson_start_end])
            InitSQL.get_DB().create_tables([Groups, Weeks, Days, Subjects, ExamDays, Disciplines, Lesson_start_end])

        # all(s not in l.lower() for s in ["zach_", "_zachety", "_ekzameny", "ekz_"])
        # any(s in l.lower() for s in ["zach_", "_zachety"])
        # any(s in l.lower() for s in ["_ekzameny", "ekz_"])
        result_links = [
            l for l in result_links
            if all(s not in l.lower() for s in ["zach_", "_zachety", "_ekzameny", "ekz_"])
               and search(r"\d([-_])?(kurs|k)[^/]*\.xls", l.lower())
        ]

        seen = set()
        result_links = [x for x in result_links if x.split('/')[-1] not in seen and not seen.add(x.split('/')[-1])]
        del seen

        parsed_tables = 0
        tables_count = len(result_links)

        for x in result_links:
            for _try in range(number_of_tries):
                req = get(x)
                if req.status_code == 200:
                    if _try != 0:
                        files_parsed.pop()
                    files_parsed.append(True)
                    md5_hash = md5(req.content).hexdigest()
                    if Parser._schedule_info.get(x.split('/')[-1], None) != md5_hash or \
                            parse_all_files_anyway:
                        print(Fore.LIGHTGREEN_EX + f"Бот парсит файл {x.split('/')[-1]}" + Style.RESET_ALL)
                        try:
                            Parser._parse_table_to_DB(req.content)
                            print(Fore.GREEN + f"Бот пропарсил файл {x.split('/')[-1]}" + Style.RESET_ALL)
                            Parser._schedule_info[x.split('/')[-1]] = md5_hash
                            Config.set_schedule_info(Parser._schedule_info)
                            Config.save_config()
                        except BaseException as ex:
                            print(Fore.RED +
                                  f"Ошибка {type(ex).__name__}: {', '.join(ex.args)} при парсинге файла {x.split('/')[-1]}!" +
                                  " Пропускаем...\nЕсли ошибка появляется больше 1-го раза," +
                                  " Вам следует обратиться к разработчику" + Style.RESET_ALL)
                    else:
                        print(Fore.GREEN +
                              f"Хеш файла {x.split('/')[-1]} идентичен. Пропускаем..." + Style.RESET_ALL)
                        hashed_files += 1
                    break
                else:
                    if _try != 0:
                        files_parsed.pop()
                    files_parsed.append(False)
                    print(Fore.RED + f"Ошибка {req.status_code} при скачивании файла {x.split('/')[-1]}!" +
                          (f' Осталось попыток - {str(number_of_tries - _try - 1)}'
                           if (number_of_tries - _try - 1) != 0 else '') + Style.RESET_ALL)
                    sleep(1)
            parsed_tables += 1
            Parser._parsed_percent = round((parsed_tables / tables_count) * 100, 1)
        if not any(files_parsed):
            print(Fore.LIGHTRED_EX + "Ни одного файла не удалось скачать! Сраные серваки МИРЭА..." + Style.RESET_ALL)
        Parser._lesson_times_parsed_for_table = False
        Parser._bot_parsing = False
        if len(files_parsed) - hashed_files > 0:
            Config.set_last_parsed_date(Parser._parsed_date)
            Config.save_config()
        else:
            Parser._parsed_date = last_parsed_date
        return all(files_parsed)

    @staticmethod
    def _parse_table_to_DB(table_contents) -> None:
        """Обработка скачанного расписания в базу данных

        Parameters
        ----------
        table_contents: bytes
            содержимое в виде набора байт скачанной таблицы
        """
        book = open_workbook(file_contents=table_contents)
        sheet_index = 1
        for sheet in book.sheets():
            print(Fore.LIGHTYELLOW_EX + f"Парсим {sheet_index} лист" + Style.RESET_ALL)
            try:
                Parser._parse_table_sheet_to_DB(sheet)
            except BaseException as ex:
                print(Fore.RED + f"Ошибка при парсинге листа {sheet_index}:" + Style.RESET_ALL)
                print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)
            sheet_index += 1
            Parser._lesson_times_parsed_for_table = False

    @staticmethod
    def _parse_table_sheet_to_DB(sheet: Sheet) -> None:
        """Обработка листа из таблицы в базу данных

        Parameters
        ----------
        sheet: Sheet
            лист из таблицы
        """
        num_cols = sheet.ncols
        # Check if several columns in the beginning are duplicating
        start_offset = 0
        first_col = sheet.col_slice(start_offset, 0, 4)
        for col in range(1, num_cols):
            curr_col = sheet.col_slice(col, 0, 4)
            if all(first_col[i].value != curr_col[i].value for i in range(1, len(first_col))):
                start_offset = col - 1
                break

        try:
            dates_cell = Parser._get_cell_info(1, 0, sheet).lower()
            regular_sheet = "день" in dates_cell
        except IndexError:
            regular_sheet = True
        print(Fore.YELLOW + f"Парсим {'обычный лист' if regular_sheet else 'экзаменационный лист'}!" + Style.RESET_ALL)

        if regular_sheet:
            Parser._parse_regular_sheet(sheet, start_offset)
        else:
            Parser._parse_exam_sheet(sheet)

    @staticmethod
    def _parse_regular_sheet(sheet: Sheet, start_offset: int):
        """Обработка листа с обычным расписанием из таблицы в базу данных

        Parameters
        ----------
        sheet: Sheet
            лист из таблицы
        start_offset: int
            начальный оффсет для дат пар
        """
        num_cols = sheet.ncols
        group_count = -1
        day_count = -1
        print_status_in = num_cols // 15

        group_max_count = Weeks.select(fn.MAX(Weeks.days_of_group_id)).scalar()
        if group_max_count is not None and group_max_count > 0:
            group_count = group_max_count
        day_max_count = Days.select(fn.MAX(Days.subject_schedules_of_day_id)).scalar()
        if day_max_count is not None and day_max_count > 0:
            day_count = day_max_count

        for col_index in range(num_cols):
            if col_index % print_status_in == 0:
                print(Fore.YELLOW + f"Прогресс: {int((col_index / num_cols) * 100)}%" + Style.RESET_ALL)
            group_cell = str(sheet.cell(1, col_index).value)
            if search(r'.{4}-\d{2}-\d{2}', group_cell):
                group_cell = findall(r'.{4}-\d{2}-\d{2}', group_cell)[0]
            else:
                continue

            try:
                group_id = Groups.get(Groups.group == group_cell).group_id
            except DoesNotExist:
                g = Groups.create(group=group_cell)
                group_id = g.group_id

            try:
                has_url = str(sheet.cell(2, col_index + 4).value).strip(".…, \n") == "Ссылка"
            except IndexError:  # Sometimes gives 'array index out of range'...
                has_url = False

            skip_to_curr_day = 0
            lesson_numbers_parsed = []

            for day in range(6):
                number_of_lessons = Parser._get_number_of_lessons(3 + skip_to_curr_day, 0, sheet)
                for lesson in range(number_of_lessons):
                    for evenness in range(2):
                        try:
                            lesson_number = int(float(Parser._get_cell_info(3 + lesson * 2 + skip_to_curr_day,
                                                                            start_offset + 1, sheet)))
                        except ValueError:
                            lesson_number = lesson + 1
                        if not Parser._lesson_times_parsed_for_table and lesson_number not in lesson_numbers_parsed:
                            lesson_numbers_parsed.append(lesson_number)
                            lesson_start_time = Parser._get_cell_info(3 + lesson * 2 + skip_to_curr_day,
                                                                      start_offset + 2, sheet)
                            lesson_end_time = Parser._get_cell_info(3 + lesson * 2 + skip_to_curr_day,
                                                                    start_offset + 3, sheet)
                            lesson_start_time = time(*map(int, lesson_start_time.split('-')))
                            lesson_end_time = time(*map(int, lesson_end_time.split('-')))
                            Parser._fill_lesson_start_end_table(lesson_number, lesson_start_time, lesson_end_time)

                        subject = Parser._get_cell_info(3 + evenness + lesson * 2 + skip_to_curr_day,
                                                        col_index, sheet)
                        lesson_type = Parser._get_cell_info(3 + evenness + lesson * 2 + skip_to_curr_day,
                                                            col_index + 1, sheet)
                        lecturer = Parser._get_cell_info(3 + evenness + lesson * 2 + skip_to_curr_day,
                                                         col_index + 2, sheet).replace(",", "\n")
                        lecturer = sub(r"[\t ]*\n+[\t ]*", "\n", lecturer)
                        classroom = Parser._get_cell_info(3 + evenness + lesson * 2 + skip_to_curr_day,
                                                          col_index + 3, sheet).replace(",", "\n")
                        classroom = sub(r"[\t ]*\n+[\t ]*", "\n", classroom)
                        if has_url:
                            url = Parser._get_cell_info(3 + evenness + lesson * 2 + skip_to_curr_day,
                                                        col_index + 4, sheet)
                        else:
                            url = ""

                        day_of_week_id = (group_count + 1) \
                            if lesson == 0 and day == 0 else (group_count - int(not bool(evenness)))
                        schedule_of_subject_id = (day_count + 1) \
                            if lesson == 0 else (day_count - int(not bool(evenness)))

                        # Check if subject exists
                        query = (
                            Weeks
                            .select(Subjects)
                            .join(Days, on=(Days.day_of_week_id == Weeks.days_of_group_id))
                            .join(Subjects, on=(Subjects.schedule_of_subject_id == Days.subject_schedules_of_day_id))
                            .where(
                                (Weeks.group_id == group_id) &
                                (Weeks.even == bool(evenness)) &
                                (Days.day_of_week == Parser._week_days[day]) &
                                (Subjects.lesson_number == lesson_number)
                            )
                            .limit(1)
                        )
                        query_list = list(query.execute())
                        if len(query_list) > 0:
                            s = query_list.pop()
                            s: Subjects = s.days.subjects
                            # Found existing
                            if s.subject != subject or s.lesson_type != lesson_type or s.teacher != lecturer or \
                                    s.class_number != classroom or s.link != url:
                                # print(f"Обновляем " +
                                #       ', '.join(
                                #           [str(lesson_number), subject, lesson_type, lecturer, classroom, url])
                                #       + " в subject_id {str(existing_records[evenness]['subject_id'])}")
                                s.subject = subject
                                s.lesson_type = lesson_type
                                s.teacher = lecturer
                                s.class_number = classroom
                                s.link = url
                                s.save()
                            continue
                        else:
                            Subjects.create(schedule_of_subject_id=schedule_of_subject_id,
                                            lesson_number=lesson_number,
                                            subject=subject,
                                            lesson_type=lesson_type,
                                            teacher=lecturer,
                                            class_number=classroom,
                                            link=url)

                        # Check if day exists
                        query = (
                            Weeks
                            .select(Days.id)
                            .join(Days, on=(Days.day_of_week_id == Weeks.days_of_group_id))
                            .where(
                                (Weeks.group_id == group_id) &
                                (Weeks.even == bool(evenness)) &
                                (Days.day_of_week == Parser._week_days[day])
                            )
                            .limit(1)
                        )
                        query_list = list(query.execute())
                        if len(query_list) > 0:
                            continue
                        else:
                            Days.create(day_of_week_id=day_of_week_id,
                                        day_of_week=Parser._week_days[day],
                                        subject_schedules_of_day_id=day_count + 1)
                            day_count += 1

                        # Check if week exists
                        query = (
                            Weeks
                            .select(Weeks.week_id)
                            .where(
                                (Weeks.group_id == group_id) &
                                (Weeks.even == bool(evenness))
                            )
                            .limit(1)
                        )
                        query_list = list(query.execute())
                        if len(query_list) == 0:
                            Weeks.create(group_id=group_id,
                                         even=bool(evenness),
                                         days_of_group_id=group_count + 1)
                            group_count += 1
                skip_to_curr_day += number_of_lessons * 2

            Parser._lesson_times_parsed_for_table = True

    @staticmethod
    def _parse_exam_sheet(sheet: Sheet):
        """Обработка листа с экзаменационным расписанием из таблицы в базу данных

        Parameters
        ----------
        sheet: Sheet
            лист из таблицы
        """
        num_cols = sheet.ncols
        print_status_in = num_cols // 15
        discipline_count = -1

        discipline_max_count = Disciplines.select(fn.MAX(Disciplines.discipline_id)).scalar()
        if discipline_max_count is not None and discipline_max_count > 0:
            discipline_count = discipline_max_count

        for col_index in range(num_cols):
            if col_index % print_status_in == 0:
                print(Fore.YELLOW + f"Прогресс: {int((col_index / num_cols) * 100)}%" + Style.RESET_ALL)
            group_cell = str(sheet.cell(1, col_index).value)
            if search(r'.{4}-\d{2}-\d{2}', group_cell):
                group_cell = findall(r'.{4}-\d{2}-\d{2}', group_cell)[0]
            else:
                continue

            try:
                group_id = Groups.get(Groups.group == group_cell).group_id
            except DoesNotExist:
                g = Groups.create(group=group_cell)
                group_id = g.group_id

            try:
                has_url = str(sheet.cell(1, col_index + 3).value).strip(".…, \n") == "Ссылка"
            except IndexError:  # Sometimes gives 'array index out of range'...
                has_url = False

            row_index = 2
            while (month := sub(r"\W+", "", Parser._get_cell_info(row_index, 0, sheet))) != "":
                month_date = date_parse(month)
                if month_date is None:
                    print(Fore.RED + f"Дата месяца '{month}' не была распарсена! Скипаем ряд..." + Style.RESET_ALL)
                    continue
                day_match = search(r"^\d{1,2}", Parser._get_cell_info(row_index, 1, sheet))
                if day_match is None:
                    print(Fore.RED + f"Дата дня '{Parser._get_cell_info(row_index, 1, sheet)}' "
                                     "не была найдена! Скипаем ряд..." + Style.RESET_ALL)
                    continue
                day_date = month_date.replace(day=int(day_match.group(0))).date()

                # Find whether day is 1-row or 3-row
                one_row_cell = Parser._get_merged_cell_info(row_index, 1, sheet)[0] is None

                discipline = ""
                discipline_type = ""
                discipline_time = None
                discipline_time_end = None
                examiner = ""
                class_number = ""
                link = ""
                if not one_row_cell:
                    flipped_time_with_classroom = False
                    if search(r"(?i).*прием.*задолженност.*", Parser._get_cell_info(row_index, col_index, sheet)):
                        discipline = Parser._get_cell_info(row_index, col_index, sheet)
                        discipline_time = time(9, 0)
                        discipline_time_end = time(18, 0)
                    else:
                        discipline_type = Parser._get_cell_info(row_index, col_index, sheet)
                        d_time = Parser._get_cell_info(row_index, col_index + 1, sheet)
                        if len(d_time) > 0:
                            for _ in range(2):
                                if match := search(
                                        r"(?P<start_hour>\d{1,2})\D(?P<start_minute>\d{1,2})\D+"
                                        r"(?P<end_hour>\d{1,2})\D(?P<end_minute>\d{1,2})",
                                        d_time
                                ):
                                    discipline_time = time(*map(int, [match.group("start_hour"),
                                                                      match.group("start_minute")]))
                                    discipline_time_end = time(*map(int, [match.group("end_hour"),
                                                                          match.group("end_minute")]))
                                    break
                                elif match_s := search(r"(?P<start_hour>\d{1,2})\D(?P<start_minute>\d{1,2})", d_time):
                                    discipline_time = time(*map(int, [match_s.group("start_hour"),
                                                                      match_s.group("start_minute")]))
                                    break
                                else:
                                    # Try different cell...
                                    if not flipped_time_with_classroom:
                                        class_number = d_time
                                        d_time = Parser._get_cell_info(row_index, col_index + 2, sheet)
                                        flipped_time_with_classroom = True
                                        continue
                                    print(Fore.RED + f"Не распарсена дата '{d_time}'! Ставим 00:00 :) "
                                                     f"Ряд - {row_index}, колонка - {col_index + 1}!" + Style.RESET_ALL)
                                    discipline_time = time(0, 0)
                        else:
                            discipline_time = None
                        discipline = Parser._get_cell_info(row_index + 1, col_index, sheet)
                        examiner = Parser._get_cell_info(row_index + 2, col_index, sheet)
                        if not flipped_time_with_classroom:
                            class_number = Parser._get_cell_info(row_index, col_index + 2, sheet)
                        if has_url:
                            link = Parser._get_cell_info(row_index, col_index + 3, sheet)
                    row_index += 3
                else:
                    row_index += 1

                if len([i for i in ExamDays.select().where(
                        (ExamDays.group_id == group_id) &
                        (ExamDays.day_date == day_date)).limit(1).execute()]) == 0:
                    ExamDays.create(
                        group_id=group_id,
                        day_date=day_date,
                        discipline_id=discipline_count + 1
                    )
                    discipline_count += 1
                    discipline_id = discipline_count
                else:
                    discipline_id = ExamDays.get((ExamDays.group_id == group_id) &
                                                 (ExamDays.day_date == day_date)).discipline_id

                if len([i for i in Disciplines.select()
                        .where(Disciplines.discipline_id == discipline_id).limit(1).execute()]) == 0:
                    # print("Создаём " +
                    #       ', '.join([str(discipline_time), discipline, discipline_type, examiner, class_number, link])
                    #       + f" в discipline_id {str(discipline_id)}")
                    Disciplines.create(
                        discipline_id=discipline_id,
                        discipline=discipline,
                        discipline_type=discipline_type,
                        discipline_time=discipline_time,
                        discipline_time_end=discipline_time_end,
                        examiner=examiner,
                        class_number=class_number,
                        link=link
                    )
                else:
                    d: Disciplines = Disciplines.get(Disciplines.discipline_id == discipline_id)
                    if d.discipline != discipline or d.discipline_type != discipline_type or \
                            d.discipline_time != discipline_time or d.discipline_time_end != discipline_time_end or \
                            d.examiner != examiner or d.class_number != class_number or d.link != link:
                        # print(f"Обновляем " +
                        #       ', '.join(
                        #           [str(discipline_time), discipline, discipline_type, examiner, class_number, link])
                        #       + " в discipline_id {str(discipline_id)}")
                        d.discipline = discipline
                        d.discipline_type = discipline_type
                        d.discipline_time = discipline_time
                        d.discipline_time_end = discipline_time_end
                        d.examiner = examiner
                        d.class_number = class_number
                        d.link = link
                        d.save()

    @staticmethod
    def _fill_lesson_start_end_table(lesson_number: int, start_time: time, end_time: time) -> None:
        """Заполнение таблицы 'Lesson_start_end' в базе данных
        Parameters
        ----------
        lesson_number: int
            номер пары
        start_time: time
            время начала пары
        end_time: time
            время конца пары
        """
        lesson_times = None
        if len([i for i in Lesson_start_end.select()
                .where(Lesson_start_end.lesson_number == lesson_number).execute()]) != 0:
            lesson_times = Lesson_start_end.get(Lesson_start_end.lesson_number == lesson_number)
        if lesson_times is None:
            Lesson_start_end.create(lesson_number=lesson_number, start_time=start_time, end_time=end_time)
        elif lesson_times.lesson_number != lesson_number or lesson_times.start_time != start_time or \
                lesson_times.end_time != end_time:
            lesson_times.lesson_number = lesson_number
            lesson_times.start_time = start_time
            lesson_times.end_time = end_time
            lesson_times.save()

    @staticmethod
    def _get_cell_info(row_index, col_index, sheet) -> str:
        """Получение информации из ячейки и проверка не является ли ячейка совмещённой
        Parameters
        ----------
        row_index: int
            номер ряда
        col_index: int
            номер колонки
        sheet: Sheet
            лист для поиска
        """
        cell = sub(r"[\t ]*\n+[\t ]*", "\n", str(sheet.cell(row_index, col_index).value).strip(".…, \n"))
        cell = sub(r"[^\S\r\n]{2,}", " ", cell)
        if cell == "":
            for crange in sheet.merged_cells:
                rlo, rhi, clo, chi = crange
                if rlo <= row_index < rhi and clo <= col_index < chi:
                    c_cell = sub(r"[\t ]*\n+[\t ]*", "\n", str(sheet.cell(rlo, clo).value).strip(".…, \n"))
                    return sub(r"[^\S\r\n]{2,}", " ", c_cell)
        return cell

    @staticmethod
    def _get_merged_cell_info(row_index, col_index, sheet):
        """Получение информации из совмещённой ячейки
        Parameters
        ----------
        row_index: int
            номер ряда
        col_index: int
            номер колонки
        sheet: Sheet
            лист для поиска
        """
        for crange in sheet.merged_cells:
            rlo, rhi, clo, chi = crange
            if rlo <= row_index < rhi and clo <= col_index < chi:
                return rhi - rlo, chi - clo
        return None, None

    @staticmethod
    def _get_number_of_lessons(row_index, col_index, sheet) -> int:
        """Получение количества пар на день
        Parameters
        ----------
        row_index: int
            номер ряда
        col_index: int
            номер колонки
        sheet: Sheet
            лист для поиска
        """
        for crange in sheet.merged_cells:
            rlo, rhi, clo, chi = crange
            if rlo <= row_index < rhi and clo <= col_index < chi:
                return (rhi - rlo) // 2
        # Workaround for 'xls' files cause 'sheet.merged_cells' is empty
        inc = 2
        while True:
            if sheet.cell(row_index + inc, col_index).value.strip() != "" or \
                    sheet.cell(row_index + inc, col_index + 1).value.strip() == "":
                break
            inc += 2
        return inc // 2
