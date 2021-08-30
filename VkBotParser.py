from contextlib import suppress
from datetime import time
from hashlib import md5
from re import search, findall

from bs4 import BeautifulSoup
from colorama import Fore, Style
from peewee import fn, DoesNotExist
from requests import get
from xlrd import open_workbook

from InitConfig import Config
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days, Subjects, Lesson_start_end


class Parser:
    """Класс Parser используется для получения расписания с сайта МИРЭА."""
    _week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    _lesson_start_end_table_filled = False
    _schedule_info = None
    _bot_parsing = False

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
    def download_schedules() -> bool:
        """Скачивает актуальное расписание с сайта МИРЭА

        Return
        ----------
        all_files_parsed: bool
            пропарсены все ли файлы
        """
        Parser._bot_parsing = True
        files_parsed = []
        result_links = []
        parse_all_files_anyway = False
        number_of_tries = 3
        if Parser._schedule_info is None:
            Parser._schedule_info = Config.get_schedule_info()
        # Parsing html page for links
        page = get("https://www.mirea.ru/schedule/")
        soup = BeautifulSoup(page.text, "html.parser")
        uni_names = soup.find("div", {"class": "rasspisanie"}).find_all("a", {"class": "uk-text-bold"})
        uni_names = list(set([i.contents[0] for i in uni_names]))
        with suppress(ValueError):
            uni_names.remove("Институт вечернего и заочного образования")
        for name in uni_names:
            links = soup.find("div", {"class": "rasspisanie"}). \
                find(string=name). \
                find_parent("div"). \
                find_parent("div"). \
                findAll("a", {"class": "uk-link-toggle"})
            links = [link["href"] for link in links]
            if len(links) > 0:
                result_links.extend(links)

        tables_length = [
            len([i for i in Weeks.select().limit(1).execute()]),
            len([i for i in Days.select().limit(1).execute()]),
            len([i for i in Subjects.select().limit(1).execute()])
        ]

        if any([i == 0 for i in tables_length]) and not all([i == 0 for i in tables_length]):
            print(Fore.LIGHTRED_EX +
                  "Одна из таблиц 'Weeks', 'Days' или 'Subjects' оказалась пуста! Заполняем все снова!" +
                  Style.RESET_ALL)
            parse_all_files_anyway = True
            InitSQL.get_DB().drop_tables([Weeks, Days, Subjects, Lesson_start_end])
            InitSQL.get_DB().create_tables([Weeks, Days, Subjects, Lesson_start_end])

        for x in result_links:
            if not any(i in x.lower() for i in ["зач", "экз", "сессия"]) and ".xls" in x.lower() and \
                    any([k_string.format(i) in x.lower() for i in range(1, 6) for k_string in
                         ["{}к", "{} курс", "{}_курс"]]):
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
                        break
                    else:
                        if _try != 0:
                            files_parsed.pop()
                        files_parsed.append(False)
                        print(Fore.RED + f"Ошибка {req.status_code} при скачивании файла {x.split('/')[-1]}!" +
                              (f' Осталось попыток - {str(number_of_tries - _try - 1)}'
                               if (number_of_tries - _try - 1) != 0 else '') + Style.RESET_ALL)
        if not any(files_parsed):
            print(Fore.LIGHTRED_EX + "Ни одного файла не удалось скачать! Сраные серваки МИРЭА..." + Style.RESET_ALL)
        Parser._lesson_start_end_table_filled = False
        Parser._bot_parsing = False
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
        sheet = book.sheet_by_index(0)
        num_cols = sheet.ncols
        # Check if several columns in the beginning are duplicating
        start_offset = 0
        first_col = sheet.col_slice(start_offset, 0, 4)
        for col in range(1, num_cols):
            curr_col = sheet.col_slice(col, 0, 4)
            if all(first_col[i].value != curr_col[i].value for i in range(len(first_col))):
                start_offset = col - 1
                break
        group_count = -1
        day_count = -1
        print_status_in = num_cols // 15

        existing_records = [
            {
                "day_id": None,
                "subject_id": None
            },
            {
                "day_id": None,
                "subject_id": None
            }
        ]

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

            for day in range(6):
                for lesson in range(6):
                    for evenness in range(2):
                        lesson_number = int(sheet.cell(3 + lesson * 2 + day * 12, start_offset + 1).value)
                        if not Parser._lesson_start_end_table_filled:
                            lesson_start_time = str(sheet.cell(3 + lesson * 2 + day * 12, start_offset + 2).value)
                            lesson_end_time = str(sheet.cell(3 + lesson * 2 + day * 12, start_offset + 3).value)
                            lesson_start_time = time(*map(int, lesson_start_time.split('-')))
                            lesson_end_time = time(*map(int, lesson_end_time.split('-')))
                            Parser._fill_lesson_start_end_table(lesson_number, lesson_start_time, lesson_end_time)

                        subject = str(sheet.cell(3 + evenness + lesson * 2 + day * 12, col_index).value).strip()
                        lesson_type = str(sheet.cell(3 + evenness + lesson * 2 + day * 12, col_index + 1).value) \
                            .strip()
                        lecturer = str(sheet.cell(3 + evenness + lesson * 2 + day * 12, col_index + 2).value) \
                            .replace(",", ".").strip()
                        classroom = str(sheet.cell(3 + evenness + lesson * 2 + day * 12, col_index + 3).value) \
                            .strip()
                        url = str(sheet.cell(3 + evenness + lesson * 2 + day * 12, col_index + 4).value).strip()

                        day_of_week_id = (group_count + 1) if lesson == 0 and day == 0 else (
                                group_count - int(not bool(evenness)))
                        schedule_of_subject_id = (day_count + 1) if lesson == 0 else (
                                day_count - int(not bool(evenness)))

                        try:
                            day_id = Weeks.get(
                                (Weeks.group == group_cell) & (Weeks.even == bool(evenness))).days_of_group_id
                            existing_records[evenness]["day_id"] = day_id
                        except DoesNotExist:
                            existing_records[evenness]["day_id"] = None

                        try:
                            subject_id = Days.get((Days.day_of_week_id == existing_records[evenness]["day_id"]) & (
                                    Days.day_of_week == Parser._week_days[day])).subject_schedules_of_day_id
                            existing_records[evenness]["subject_id"] = subject_id
                        except DoesNotExist:
                            existing_records[evenness]["subject_id"] = None

                        if len([i for i in Subjects.select().where(
                                (Subjects.schedule_of_subject_id == existing_records[evenness]["subject_id"]) &
                                (Subjects.lesson_number == lesson_number)).execute()]) == 0:
                            # print("Создаём " +
                            #       ', '.join([str(lesson_number), subject, lesson_type, lecturer, classroom, url])
                            #       + f" в subject_id {str(schedule_of_subject_id)}")
                            Subjects.create(schedule_of_subject_id=schedule_of_subject_id,
                                            lesson_number=lesson_number,
                                            subject=subject,
                                            lesson_type=lesson_type,
                                            teacher=lecturer,
                                            class_number=classroom,
                                            link=url)
                        else:
                            s = Subjects.get(
                                (Subjects.schedule_of_subject_id == existing_records[evenness]["subject_id"]) &
                                (Subjects.lesson_number == lesson_number))
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

                        if len([i for i in Days.select().where(
                                (Days.day_of_week_id == existing_records[evenness]["day_id"]) &
                                (Days.day_of_week == Parser._week_days[day])).execute()]) == 0:
                            if len([i for i in Days.select().where(
                                    (Days.day_of_week_id == day_of_week_id) &
                                    (Days.day_of_week == Parser._week_days[day])).execute()]) == 0:
                                Days.create(day_of_week_id=day_of_week_id,
                                            day_of_week=Parser._week_days[day],
                                            subject_schedules_of_day_id=day_count + 1)
                                day_count += 1

                        if len([i for i in Weeks.select().where(
                                (Weeks.group == group_cell) & (Weeks.even == bool(evenness))).execute()]) == 0:
                            Weeks.create(group=group_cell,
                                         even=bool(evenness),
                                         days_of_group_id=group_count + 1)
                            group_count += 1

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
        if lesson_number == 6:
            Parser._lesson_start_end_table_filled = True
