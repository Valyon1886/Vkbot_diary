import datetime
import xlrd
import re
import json
import requests
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bs4 import BeautifulSoup
from os.path import exists

# TODO:
#  Отображение расписания с сайта
#  Поддержка голосового ввода
#  Загрузка расписания в бд (после этого можно будет добавлять заметки)
#  1 Расписание 2. Пользователи/настройки 3. Заметки
#  Добавление заметок (напротив предмета, см таблицу)
#  Добавление своих пунктов в расписание (см таблицу)
#  Вывод расписания из бд (на сегодня/на неделю)
#  Обновление расписания в бд (с сохранением записей пользователя) !!!!!!!!!!!!!!!!!
#  Случайный мем

schedules = dict()
users = dict()
week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]


# TODO:
#  Почистить код
#  Сделать конф файл
#  Переписать по класам


def schedule():
    page = requests.get("https://www.mirea.ru/schedule/")
    soup = BeautifulSoup(page.text, "html.parser")
    result = soup.find("div", {"class": "rasspisanie"}).find(string="Институт информационных технологий"). \
        find_parent("div").find_parent("div").findAll("a", {"class": "uk-link-toggle"})
    for x in result:
        for i in range(1, 4):
            if re.search(r'https://webservices.mirea.ru/upload/iblock/366/ИИТ_2к_20-21_весна.xlsx', str(x)):
                f = open("schedule" + str(i) + ".xlsx", "wb")
                if x["href"] != schedules["link"][i - 1]:
                    filexlsx = requests.get(x["href"])
                    f.write(filexlsx.content)
                    f.close()
                    parse_table("schedule" + str(i) + ".xlsx")
                    schedules["link"][i - 1] = x["href"]
    json.dump(schedules, open("schedules_cache.json", "w"))


def parse_table(table):
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
                day = [[], [], [], [], [], []]
                for i in range(6):
                    for j in range(2):
                        subject = sheet.cell(3 + j + i * 2 + k * 12, col_index).value
                        lesson_type = sheet.cell(3 + j + i * 2 + k * 12, col_index + 1).value
                        lecturer = sheet.cell(3 + j + i * 2 + k * 12, col_index + 2).value
                        lecturer = lecturer.replace(",", ".")
                        classroom = sheet.cell(3 + j + i * 2 + k * 12, col_index + 3).value
                        url = sheet.cell(3 + j + i * 2 + k * 12, col_index + 4).value
                        lesson = {"subject": subject, "lesson_type": lesson_type,
                                  "lecturer": lecturer, "classroom": classroom, "url": url}
                        day[i].append(lesson)
                week[week_days[k]] = day
            groups.update({group_cell: week})
    schedules["groups"].update(groups)
    json.dump(schedules, open("schedules_cache.json", "w"))


def send_message(vk_session, id, rand_id, message=None, keyboard=None):
    vk_session.method('messages.send', {'user_id': id, 'message': message, 'random_id': rand_id, 'keyboard': keyboard})


def send_pic(vk_session, id, response):
    response.save('img.png')
    upload = VkUpload(vk_session)
    photo = upload.photo_messages('img.png')
    image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
    vk_session.method('messages.send', {'user_id': id, 'random_id': get_random_id(), "attachment": image})


def menu(response):
    keyboard = VkKeyboard(one_time=True)

    if response == 'Продолжить':
        keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)

    if response == 'расписание':
        keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Какая неделя?')
        keyboard.add_button('Какая группа?')

    keyboard = keyboard.get_keyboard()
    return keyboard


def schedule_menu(response, vk_session, id, rand_id):
    if response == "на сегодня":
        week_day = datetime.datetime.now().isoweekday() - 1
        if week_day < 6:
            week_day = week_days[week_day]
            student_group = schedules["groups"][users[str(id)]]
            full_sentence = make_schedule(week_day, student_group)
            send_message(vk_session, id, rand_id, message='Расписание на сегодня:\n' + week_day + '\n' + full_sentence)
        else:
            send_message(vk_session, id, rand_id, message='Выходной')
    if response == "на завтра":
        week_day = datetime.datetime.now().isoweekday()
        if week_day == 7:
            week_day = 0
        if week_day < 6:
            week_day = week_days[week_day]
            student_group = schedules["groups"][users[str(id)]]
            full_sentence = make_schedule(week_day, student_group)
            send_message(vk_session, id, rand_id, message='Расписание на завтра:\n' + week_day + '\n' + full_sentence)
        else:
            send_message(vk_session, id, rand_id, message='Выходной')
    if response == "на эту неделю":
        full_sentence = ""
        for i in range(len(week_days)):
            week_day = week_days[i]
            student_group = schedules["groups"][users[str(id)]]
            full_sentence += '\n' + week_day + ':\n' + make_schedule(week_day, student_group) + '\n\n'
        send_message(vk_session, id, rand_id, message='Расписание на эту неделю: ' + full_sentence)
    if response == "на следующую неделю":
        full_sentence = ""
        for i in range(len(week_days)):
            week_day = week_days[i]
            student_group = schedules["groups"][users[str(id)]]
            full_sentence += '\n' + week_day + ':\n' + make_schedule(week_day, student_group, 1) + '\n\n'
        send_message(vk_session, id, rand_id, message='Расписание на следующую неделю: ' + full_sentence)
    if response == "какая неделя?":
        send_message(vk_session, id, rand_id,
                     message='Сейчас ' + str(number_week(datetime.datetime.now())) + ' неделя.')
    if response == "какая группа?":
        send_message(vk_session, id, rand_id, message='Твоя группа ' + users[str(id)])


def number_week(day_today):
    first_week = datetime.datetime(2020, 2, 10).isocalendar()[1]
    current_week = day_today.isocalendar()[1]
    number = current_week - first_week
    return number


def make_schedule(week_day, student_group, next_week=0):
    schedules_group = student_group[week_day]
    chet_week = (number_week(datetime.datetime.now()) + next_week) % 2
    full_sentence = ""
    for i in range(len(schedules_group)):
        if not schedules_group[i][chet_week]['subject']:
            full_sentence = full_sentence + str(i + 1) + ') --\n'
        else:
            full_sentence = full_sentence + str(i + 1) + ') ' + \
                            schedules_group[i][chet_week]['subject'] + ' ' + \
                            schedules_group[i][chet_week]['lesson_type'] + '.'
            if schedules_group[i][chet_week]['lecturer']:
                full_sentence = full_sentence + ' Преподаватель: ' + schedules_group[i][chet_week]['lecturer']
            if schedules_group[i][chet_week]['url']:
                full_sentence = full_sentence + '\nСсылка: ' + schedules_group[i][chet_week]['url']
            full_sentence = full_sentence + '\n'
    return full_sentence


def main():
    global schedules, users, week_days
    if exists("./schedules_cache.json"):
        schedules = json.load(open("schedules_cache.json", "r"))
    else:
        schedules = {'link': [1, 1, 1], 'groups': {}}
    if exists("./users_cache.json"):
        users = json.load(open("users_cache.json", "r"))
    schedule()

    vk_session = vk_api.VkApi(
        token='ad471dd1cad0f1ee579114a1c2a9a4de239fa03c529db7de8969d3df199aff15c6afc3a9ce2bd1dbb19a1')
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            response = event.text.lower()
            keyboard = menu(response)

            if response == 'начать':
                send_message(vk_session, event.user_id, get_random_id(),
                             message='Привет, ' + vk.users.get(user_id=event.user_id)[0]['first_name'] +
                             '\nНапиши свою группу\nФорма записи группы: ИКБО-09-19')
                response = 'Продолжить'
                keyboard = menu(response)

            elif re.search(r'([а-я]{2}бо-\d{2}-\d{2})', response):
                if response.upper() in schedules["groups"]:
                    users[str(event.user_id)] = response.upper()
                    json.dump(users, open("users_cache.json", "w"))
                    send_message(vk_session, event.user_id, get_random_id(),
                                 message='Группа сохранена! Номер твоей группы: ' + users[str(event.user_id)])
                else:
                    send_message(vk_session, event.user_id, get_random_id(),
                                 message='Такой группы нет, попробуй еще раз.')
                response = 'Продолжить'
                keyboard = menu(response)

            elif response == 'расписание':
                send_message(vk_session, event.user_id, get_random_id(), message='Выбери возможность',
                             keyboard=keyboard)

            elif re.search(r'(на [а-я]+( [а-я]+)?)|(какая [а-я]{6})', response):
                try:
                    schedule_menu(response, vk_session, event.user_id, get_random_id())
                except KeyError:
                    send_message(vk_session, event.user_id, get_random_id(),
                                 message='Вы не ввели группу.\n Формат ввода: ИКБО-09-19')
                response = 'Продолжить'
                keyboard = menu(response)

            else:
                send_message(vk_session, event.user_id, get_random_id(), message='Я не знаю такой команды')
                response = 'Продолжить'
                keyboard = menu(response)

            if response == 'Продолжить':
                send_message(vk_session, event.user_id, get_random_id(), message='Что хочешь посмотреть?',
                             keyboard=keyboard)


if __name__ == '__main__':
    main()
