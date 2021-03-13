import re
import json

import xlrd
import requests
from bs4 import BeautifulSoup


class Parser:
    def __init__(self):
        self.week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

    def schedule(self, schedules):
        page = requests.get("https://www.mirea.ru/schedule/")
        soup = BeautifulSoup(page.text, "html.parser")
        result = soup.find("div", {"class": "rasspisanie"}). \
            find(string="Институт информационных технологий"). \
            find_parent("div"). \
            find_parent("div"). \
            findAll("a", {"class": "uk-link-toggle"})
        for x in result:
            for i in range(1, 5):
                if f"{i}к" in x["href"] and "зач" not in x["href"] and "экз" not in x["href"]:
                    if x["href"] != schedules["link"][i - 1]:
                        with open(f"local_files/schedule-{str(i)}k.xlsx", "wb") as f:
                            filexlsx = requests.get(x["href"])
                            f.write(filexlsx.content)
                        self.parse_table(f"local_files/schedule-{str(i)}k.xlsx", schedules)
                        schedules["link"][i - 1] = x["href"]
        json.dump(schedules, open("local_files/schedules_cache.json", "w"))

    def parse_table(self, table, schedules):
        groups = {}
        groups_list = []
        groups_list_all = []
        book = xlrd.open_workbook(table)
        sheet = book.sheet_by_index(0)
        num_cols = sheet.ncols
        for col_index in range(num_cols):
            group_cell = str(sheet.cell(1, col_index).value)
            reg = re.search(r'.{2}БО-\d{2}-1\d', group_cell)
            if reg:
                groups_list_all.append(reg.string)
                groups_list.append(reg.string)
                week = {"Понедельник": None, "Вторник": None, "Среда": None,
                        "Четверг": None, "Пятница": None, "Суббота": None}
                for k in range(6):
                    day = [[] for _ in range(6)]
                    for i in range(6):
                        for j in range(2):
                            subject = sheet.cell(3 + j + i * 2 + k * 12, col_index).value
                            lesson_type = sheet.cell(3 + j + i * 2 + k * 12, col_index + 1).value
                            lecturer = sheet.cell(3 + j + i * 2 + k * 12, col_index + 2).value
                            lecturer = str(lecturer).replace(",", ".")
                            classroom = sheet.cell(3 + j + i * 2 + k * 12, col_index + 3).value
                            url = sheet.cell(3 + j + i * 2 + k * 12, col_index + 4).value
                            lesson = {"subject": subject, "lesson_type": lesson_type,
                                      "lecturer": lecturer, "classroom": classroom, "url": url}
                            day[i].append(lesson)
                    week[self.week_days[k]] = day
                groups.update({group_cell: week})
        schedules["groups"].update(groups)
        json.dump(schedules, open("local_files/schedules_cache.json", "w"))