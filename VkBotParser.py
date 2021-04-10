from re import search
from os import remove
from pathlib import Path
from datetime import time
from sys import exit
from hashlib import md5

from xlrd import open_workbook
from requests import get
from bs4 import BeautifulSoup
from peewee import fn

from InitConfig import Config
from MySQLStorage import Weeks, Days, Subjects, Lesson_start_end


class Parser:
    """Класс Parser используется для получения расписания с сайта МИРЭА."""
    _week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    _lesson_start_end_table_filled = False
    _parsed_any_file = False

    def __init__(self, config: Config):
        self._config = config
        self._dir_name = self._config.get_dir_name()
        self._schedule_info = self._config.get_schedule_info()
        self._download_schedules()

    def _download_schedules(self):
        """Скачивает актуальное расписание с сайта МИРЭА."""
        page = get("https://www.mirea.ru/schedule/")
        soup = BeautifulSoup(page.text, "html.parser")
        result = soup.find("div", {"class": "rasspisanie"}). \
            find(string="Институт информационных технологий"). \
            find_parent("div"). \
            find_parent("div"). \
            findAll("a", {"class": "uk-link-toggle"})
        for x in result:
            for i in range(1, 5):
                if f"{i}к" in x["href"].lower() and "зач" not in x["href"].lower() and "экз" not in x["href"].lower():
                    req = get(x["href"])
                    if req.status_code == 200:
                        md5_hash = md5(req.content).hexdigest()
                        if self._schedule_info.get(x["href"], None) != md5_hash:
                            with open(Path(self._dir_name + f"/schedule-{str(i)}k.xlsx"), "wb") as f:
                                f.write(req.content)
                            self._parse_table_DB(Path(self._dir_name + f"/schedule-{str(i)}k.xlsx"))
                            print(f"Бот пропарсил расписание {x['href'].split('/')[-1]}")
                            if not self._parsed_any_file:
                                self._parsed_any_file = True
                            self._schedule_info[x["href"]] = md5_hash
                            remove(Path(self._dir_name + f"/schedule-{str(i)}k.xlsx"))
                        else:
                            if not self._parsed_any_file:
                                self._parsed_any_file = True
                    else:
                        print(f"Ошибка {req.status_code} при скачивании файла!")
        if not self._parsed_any_file:
            exit("Ни одного файла не удалось скачать! Сраные серваки МИРЭА...")
        else:
            self._config.set_schedule_info(self._schedule_info)
            self._config.save_config()

    def _parse_table_DB(self, table):
        """Обработка скачанного расписания в базу данных."""
        book = open_workbook(table)
        sheet = book.sheet_by_index(0)
        num_cols = sheet.ncols
        group_count = -1
        day_count = -1

        group_max_count = Weeks.select(fn.MAX(Weeks.days_of_group_id)).scalar()
        if group_max_count is not None and group_max_count > 0:
            group_count = group_max_count
        day_max_count = Days.select(fn.MAX(Days.subject_schedules_of_day_id)).scalar()
        if day_max_count is not None and day_max_count > 0:
            day_count = day_max_count

        for col_index in range(num_cols):
            group_cell = str(sheet.cell(1, col_index).value)
            if search(r'.{4}-\d{2}-\d{2}', group_cell):
                for day in range(6):
                    for lesson in range(6):
                        for evenness in range(2):
                            lesson_number = int(sheet.cell(3 + lesson * 2 + day * 12, 1).value)
                            if not self._lesson_start_end_table_filled:
                                lesson_start_time = str(sheet.cell(3 + lesson * 2 + day * 12, 2).value)
                                lesson_end_time = str(sheet.cell(3 + lesson * 2 + day * 12, 3).value)
                                lesson_start_time = time(*map(int, lesson_start_time.split('-')))
                                lesson_end_time = time(*map(int, lesson_end_time.split('-')))
                                self._fill_lesson_start_end_table(lesson_number, lesson_start_time, lesson_end_time)

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
                            # print(f"{lesson_number} {bool(evenness)} - id {schedule_of_subject_id}")
                            Subjects.create(schedule_of_subject_id=schedule_of_subject_id,
                                            lesson_number=lesson_number,
                                            subject=subject,
                                            lesson_type=lesson_type,
                                            teacher=lecturer,
                                            class_number=classroom,
                                            link=url)

                            if len([i for i in Days.select().where((Days.day_of_week_id == day_of_week_id) & (
                                    Days.day_of_week == self._week_days[day])).execute()]) == 0:
                                # print(f"{self._week_days[day]} {bool(evenness)} - id "f
                                # "{(group_count + 1) if lesson == 0 and day == 0 else (group_count - int(not bool(evenness)))}")
                                Days.create(day_of_week_id=day_of_week_id,
                                            day_of_week=self._week_days[day],
                                            subject_schedules_of_day_id=day_count + 1)
                                day_count += 1

                            if len([i for i in Weeks.select().where(
                                    (Weeks.group == group_cell) & (Weeks.even == bool(evenness))).execute()]) == 0:
                                # print(group_cell, f"Чётная: {bool(evenness)}",
                                # str((group_count - evenness) if lesson != 0 else (group_count + 1)), sep=" || ")
                                Weeks.create(group=group_cell,
                                             even=bool(evenness),
                                             days_of_group_id=group_count + 1)
                                group_count += 1

    def _fill_lesson_start_end_table(self, lesson_number: int, start_time: time, end_time: time):
        """Заполнение таблицы 'Lesson_start_end' в базе данных"""
        current_lessons = [i.lesson_number for i in Lesson_start_end.select().execute()]
        if lesson_number not in current_lessons:
            Lesson_start_end.create(lesson_number=lesson_number, start_time=start_time, end_time=end_time)
        if len(current_lessons) == 6:
            self._lesson_start_end_table_filled = True


if __name__ == '__main__':
    import time
    from peewee import DoesNotExist

    group = "ИКБО-03-19"
    # Weeks.create(group=group,
    #              even=False,
    #              day_lesson=Days.create(day_of_week='Monday',
    #                                             schedule_of_subject=Subjects.create(lesson_number='',
    #                                                                                            subject_task='',
    #                                                                                            lesson_type='',
    #                                                                                            teacher='',
    #                                                                                            class_number='',
    #                                                                                            link="")))

    # Parser().parse_table_DB(Path("local_files" + f"/schedule-{2}k.xlsx"))
    tic = time.perf_counter()
    # res = [i.day_lesson_id for i in Weeks.select().where(Weeks.group == group and Weeks.even == True)]
    result = Weeks.select(fn.MAX(Weeks.days_of_group_id)).scalar()

    try:
        day_lesson = Weeks.get((Weeks.group == group) & (Weeks.even == True)).days_of_group_id  # Для единичной выцепки
        # group = [i for i in Users.select().where(Users.user_id == self._user_id).limit(1)][0].group  # Для множественной
        # schedules_of_day = Days.get((Days.day_of_week_id == day_lesson) & (Days.day_of_week == "Понедельник")).subject_schedules_of_day_id
        schedules_of_day = [i.subject_schedules_of_day_id for i in Days.select(Days.subject_schedules_of_day_id).where(
            Days.day_of_week_id == day_lesson).execute()]
        # res = [i.subject_schedules_of_day_id for i in
        #        Days.select().where((Days.day_of_week_id == day_lesson) & (Days.day_of_week == "Понедельник")).execute()]
        for sc in schedules_of_day:
            for subject in [i for i in Subjects.select().where(Subjects.schedule_of_subject_id == sc).execute()]:
                message = f"{subject.lesson_number})\n{subject.subject}\n{subject.lesson_type}\n{subject.teacher}\n{subject.class_number}\n{subject.link}"
                print(message)
    except DoesNotExist:  # and IndexError
        print("lol DNE")
    toc = time.perf_counter()
    print(f"Selected in {toc - tic:0.5f} seconds")
    # Days.day_of_week == "Понедельник"
    # Subjects
