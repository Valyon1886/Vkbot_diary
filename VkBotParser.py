from re import search
from json import dump, load
from os.path import exists
from pathlib import Path

from xlrd import open_workbook
from requests import get
from bs4 import BeautifulSoup


class Parser:
    """Класс Parser используется для получения расписания с сайта МИРЭА."""
    _dir_name = "local_files"

    def __init__(self):
        self._week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        self._schedules = dict()
        if exists(Path(self._dir_name + "/schedules_cache.json")):
            self._schedules = load(open(Path(self._dir_name + "/schedules_cache.json"), "r"))
        else:
            self._schedules = {'link': [1 for _ in range(4)], 'groups': {}}
        self._schedule()

    def _schedule(self):
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
                    if x["href"] != self._schedules["link"][i - 1]:
                        file_xlsx = get(x["href"])
                        with open(Path(self._dir_name + f"/schedule-{str(i)}k.xlsx"), "wb") as f:
                            f.write(file_xlsx.content)
                        self._parse_table(Path(self._dir_name + f"/schedule-{str(i)}k.xlsx"))
                        self._schedules["link"][i - 1] = x["href"]
        dump(self._schedules, open(Path(self._dir_name + "/schedules_cache.json"), "w"))

    def _parse_table(self, table):
        """Обработка скачанного расписания."""
        groups = {}
        groups_list = []
        groups_list_all = []
        book = open_workbook(table)
        sheet = book.sheet_by_index(0)
        num_cols = sheet.ncols
        for col_index in range(num_cols):
            group_cell = str(sheet.cell(1, col_index).value)
            reg = search(r'.{4}-\d{2}-\d{2}', group_cell)
            if reg:
                groups_list_all.append(reg.string)
                groups_list.append(reg.string)
                week = {str(i): None for i in self._week_days}
                for k in range(6):
                    day = [[] for _ in range(6)]
                    for i in range(6):
                        for j in range(2):
                            lesson_number = int(sheet.cell(3 + i * 2 + k * 12, 1).value)
                            subject = str(sheet.cell(3 + j + i * 2 + k * 12, col_index).value).strip().replace('\n', '')
                            lesson_type = str(sheet.cell(3 + j + i * 2 + k * 12, col_index + 1).value)\
                                .strip().replace('\n', '')
                            lecturer = str(sheet.cell(3 + j + i * 2 + k * 12, col_index + 2).value)\
                                .replace(",", ".").strip().replace('\n', '')
                            classroom = str(sheet.cell(3 + j + i * 2 + k * 12, col_index + 3).value)\
                                .strip().replace('\n', '')
                            url = str(sheet.cell(3 + j + i * 2 + k * 12, col_index + 4).value).strip().replace('\n', '')
                            lesson = {"lesson_number": lesson_number, "subject": subject, "lesson_type": lesson_type,
                                      "lecturer": lecturer, "classroom": classroom, "url": url}
                            day[i].append(lesson)
                    week[self._week_days[k]] = day
                groups.update({group_cell: week})
        self._schedules["groups"].update(groups)
        dump(self._schedules, open(Path(self._dir_name + "/schedules_cache.json"), "w"))

    def get_schedules(self):
        """Получение расписания."""
        return self._schedules
