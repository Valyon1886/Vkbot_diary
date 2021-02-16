import vk_api
import xlrd
import re
import json
import datetime
from os.path import exists
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bs4 import BeautifulSoup
from urllib.request import urlopen
from PIL import Image
from vk_api import VkUpload
from pprint import pprint


schedules = dict()
users = dict()
lecturers = []
week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
WEATHER_KEY = "05cc2272c262cbc1a3a33fe296be36e0"


def schedule():
    page = requests.get("https://www.mirea.ru/schedule/")
    soup = BeautifulSoup(page.text, "html.parser")
    result = soup.find("div", {"class": "rasspisanie"}).find(string="Институт информационных технологий").\
        find_parent("div").find_parent("div").findAll("a", {"class": "uk-link-toggle"})
    for x in result:
        for i in range(1, 4):
            if re.search(r'https://webservices.mirea.ru/upload/iblock/ca4/ИИТ_2к_20-21_весна.xlsx', str(x)):
                f = open("schedule"+str(i)+".xlsx", "wb")
                if x["href"] != schedules["link"][i - 1]:
                    filexlsx = requests.get(x["href"])
                    f.write(filexlsx.content)
                    f.close()
                    parse_table("schedule"+str(i)+".xlsx")
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
                        lecturer = re.findall(r'[А-я]+ \w.\w.', lecturer)
                        if lecturer:
                            if len(lecturer) > 1:
                                for lec in range(len(lecturer)):
                                    if lecturer[lec] not in lecturers:
                                        lecturers.append(lecturer[lec])
                            elif len(lecturer) == 1:
                                if lecturer[0] not in lecturers:
                                    lecturers.append(lecturer[0])
                week[week_days[k]] = day
            groups.update({group_cell: week})
    schedules["groups"].update(groups)
    json.dump(schedules, open("schedules_cache.json", "w"))
    json.dump(lecturers, open("lecturers_cache.json", "w"))


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
        keyboard.add_button('Преподаватель', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Погода', color=VkKeyboardColor.PRIMARY)

    if response == 'расписание':
        keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Какая неделя?')
        keyboard.add_button('Какая группа?')

    if response == 'Преподаватель':
        keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)

    keyboard = keyboard.get_keyboard()
    return keyboard


def menu_weather(longpoll, vk_session, id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Сейчас', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('На неделю')
    send_message(vk_session, id, get_random_id(), message='Что хотите узнать?', keyboard=keyboard.get_keyboard())
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            response = event.text.lower()
            if response == 'сейчас':
                response = now_weather_info()
                send_pic(vk_session, id, response[1])
                send_message(vk_session, id, get_random_id(), message=response[0])
            elif response == 'на сегодня':
                response = day_weather_info(datetime.date.today())
                send_pic(vk_session, id, response[1])
                send_message(vk_session, id, get_random_id(), message=response[0])
            elif response == 'на завтра':
                response = day_weather_info(datetime.date.today() + datetime.timedelta(days=1))
                send_pic(vk_session, id, response[1])
                send_message(vk_session, id, get_random_id(), message=response[0])
            elif response == 'на неделю':
                response = week_weather_info()
                send_pic(vk_session, id, response[1])
                send_message(vk_session, id, get_random_id(), message=response[0])
            return


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
        send_message(vk_session, id, rand_id, message='Сейчас ' + str(number_week(datetime.datetime.now())) + ' неделя.')
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


def find_lecturer(longpoll, vk_session, id):
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            response = event.text.lower()
            request = []
            for i in range(len(lecturers)):
                lecturer = lecturers[i].split()
                if response == lecturer[0].lower():
                    request.append(lecturers[i])

            if len(request) > 1:
                request[0] = choose_lecturer(longpoll, vk_session, id, request)
                schedules_lecturer(longpoll, vk_session, id, request[0])
            elif len(request) == 1:
                schedules_lecturer(longpoll, vk_session, id, request[0])
            else:
                send_message(vk_session, id, get_random_id(), message='Такого преподавателя нет')
            return


def choose_lecturer(longpoll, vk_session, id, request):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(str(request[0]), color=VkKeyboardColor.PRIMARY)
    for i in range(1, len(request)):
        keyboard.add_line()
        keyboard.add_button(str(request[i]), color=VkKeyboardColor.PRIMARY)
    send_message(vk_session, id, get_random_id(), message='Выбери преподавателя', keyboard=keyboard.get_keyboard())
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            return event.text


def schedules_lecturer(longpoll, vk_session, id, request):
    keyboard = menu('Преподаватель')
    send_message(vk_session, id, get_random_id(), message='Что хотите узнать?', keyboard=keyboard)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            response = event.text.lower()
            if response == "на сегодня":
                week_day = datetime.datetime.now().isoweekday() - 1
                if week_day < 6:
                    week_day = week_days[week_day]
                    full_sentence = make_schedule_lecturer(week_day, request)
                    send_message(vk_session, id, get_random_id(), message='Расписание преподавателя ' + request
                                                                          + ' на сегодня:\n' + full_sentence)
                else:
                    send_message(vk_session, id, get_random_id(), message='Выходной')

            elif response == "на завтра":
                week_day = datetime.datetime.now().isoweekday()
                if week_day == 7:
                    week_day = 0
                if week_day < 6:
                    week_day = week_days[week_day]
                    full_sentence = make_schedule_lecturer(week_day, request)
                    send_message(vk_session, id, get_random_id(), message='Расписание преподавателя ' + request
                                                                          + ' на завтра:\n' + full_sentence)
                else:
                    send_message(vk_session, id, get_random_id(), message='Выходной')

            elif response == "на эту неделю":
                full_sentence = ""
                for i in range(len(week_days)):
                    week_day = week_days[i]
                    full_sentence += '\n' + week_day + ':\n' + make_schedule_lecturer(week_day, request) + '\n\n'
                send_message(vk_session, id, get_random_id(), message='Расписание преподавателя ' + request
                                                                      + ' на эту неделю:\n' + full_sentence)

            elif response == "на следующую неделю":
                full_sentence = ""
                for i in range(len(week_days)):
                    week_day = week_days[i]
                    full_sentence += '\n' + week_day + ':\n' + make_schedule_lecturer(week_day, request, 1) + '\n\n'
                send_message(vk_session, id, get_random_id(), message='Расписание преподавателя ' + request
                                                                      + ' на следующую неделю:\n' + full_sentence)
            return


def make_schedule_lecturer(week_day, name, next_week=0):
    full_sentence = ""
    chet_week = (number_week(datetime.datetime.now()) + next_week) % 2
    for i in range(6):
        groups = ''
        url = ''
        flag = True
        for group in schedules["groups"].keys():
            lecturer = re.findall(r'[А-я]+ \w.\w.', schedules["groups"][group][week_day][i][chet_week]["lecturer"])
            if lecturer:
                if len(lecturer) > 1:
                    for lec in range(len(lecturer)):
                        if lecturer[lec] == name:
                            if flag:
                                full_sentence = full_sentence + str(i + 1) + ') ' \
                                                + schedules["groups"][group][week_day][i][chet_week]["subject"] + ", " \
                                                + schedules["groups"][group][week_day][i][chet_week][
                                                    "lesson_type"] + ", " \
                                                + schedules["groups"][group][week_day][i][chet_week][
                                                    "classroom"] + "."
                                groups = groups + group
                                url = schedules["groups"][group][week_day][i][chet_week]["url"]
                                flag = False
                            else:
                                if groups:
                                    groups = groups + ', ' + group
                                else:
                                    groups = group
                elif len(lecturer) == 1:
                    if lecturer[0] == name:
                        if flag:
                            full_sentence = full_sentence + str(i + 1) + ') ' \
                                            + schedules["groups"][group][week_day][i][chet_week]["subject"] + ", " \
                                            + schedules["groups"][group][week_day][i][chet_week]["lesson_type"] + ", " \
                                            + schedules["groups"][group][week_day][i][chet_week][
                                                "classroom"] + "."
                            groups = groups + group
                            url = schedules["groups"][group][week_day][i][chet_week]["url"]
                            flag = False
                        else:
                            if groups:
                                groups = groups + ', ' + group
                            else:
                                groups = group
        if flag:
            full_sentence = full_sentence + str(i + 1) + ') --'
        else:
            full_sentence = full_sentence + ' Для ' + groups
            if url:
                full_sentence = full_sentence + '\nСсылка: ' + url
        full_sentence = full_sentence + '\n'
    return full_sentence


def splice(img1, img2):
    (width, height) = img1.size
    (width1, height1) = img2.size
    img = Image.new(mode = 'RGBA', size = (width + width1, height), color =  (0, 0, 0))
    img.paste(img1, (0, 0))
    img.paste(img2, (width, 0))
    return img


def weather_info(weather):
    dirs = [
        "северный",
        "северо-восточный",
        "восточный",
        "юго-восточный",
        "южный",
        "юго-западный",
        "западный",
        "северо-западный",
    ]
    direction = dirs[(weather["wind"]["deg"] % 360) // 45]
    speed = weather["wind"]["speed"] * 10
    if speed < 3:
        wind = "штиль"
    elif speed < 16:
        wind = "тихий"
    elif speed < 34:
        wind = "лёгкий"
    elif speed < 55:
        wind = "слабый"
    elif speed < 80:
        wind = "умеренный"
    elif speed < 108:
        wind = "свежий"
    elif speed < 139:
        wind = "сильный"
    elif speed < 172:
        wind = "крепкий"
    elif speed < 208:
        wind = "очень крепкий"
    elif speed < 245:
        wind = "шторм"
    elif speed < 285:
        wind = "сильный шторм"
    elif speed < 327:
        wind = "жестокий шторм"
    else:
        wind = "ураган"
    pressure = str(round(float(weather["main"]["pressure"]) * 100 / 133.3))
    temp = str(round(weather["main"]["temp"]))
    message = '//' + weather['weather'][0]['description'].capitalize() + ', температура воздуха: ' + temp + ' °C' + \
              '\n//Давление: ' + pressure + ' мм рт. ст., влажность: ' + str(weather['main']['humidity']) + \
              '\n//Ветер: ' + wind + ' ' + str(weather['wind']['speed']) + ' м/с, ' + direction
    image = Image.open(urlopen(f'http://openweathermap.org/img/wn/{weather["weather"][0]["icon"]}.png'))
    return {'text': message, 'image': image}


def now_weather_info():
    response = json.load(urlopen(f"http://api.openweathermap.org/data/2.5/forecast?"
                                 f"q=moscow&"
                                 f"appid={WEATHER_KEY}&"
                                 f"units=metric&"
                                 f"lang=ru"))
    pprint(response)
    response = response['list'][0]
    message = ''
    attachment = []
    result = []
    temp = weather_info(response)
    message = temp['text']
    attachment.append(temp['image'])
    result.append(message)
    result.append(attachment[-1])
    return result


def day_weather_info(date):
    date = date.strftime("%Y-%m-%d")
    response = json.load(urlopen(f"http://api.openweathermap.org/data/2.5/forecast?"
                                 f"q=moscow&"
                                 f"appid={WEATHER_KEY}&"
                                 f"units=metric&"
                                 f"lang=ru"))
    response = [e for e in response['list'] if e['dt_txt'].startswith(date)]
    message = ''
    attachment = []
    result = []
    con = 8 - len(response)
    for day_part, num in {"УТРО": 3, "ДЕНЬ": 4, "ВЕЧЕР": 6, "НОЧЬ": 7}.items():
        if con <= num:
            temp = weather_info(response[num - con])
            message = message + day_part + '\n' + temp['text'] + '\n'
            attachment.append(temp['image'])
    for i in range(1, len(attachment)):
        attachment[i] = splice(attachment[i-1], attachment[i])
    result.append(message)
    result.append(attachment[-1])
    return result


def week_weather_info():
    response = json.load(urlopen(f"http://api.openweathermap.org/data/2.5/forecast?"
                                 f"q=moscow&"
                                 f"appid={WEATHER_KEY}&"
                                 f"units=metric&"
                                 f"lang=ru"))
    response = response['list']
    image = None
    day = -1
    night = -1
    k = 0
    while day < 0 or night < 0:
        if response[k]['dt_txt'].endswith("12:00:00"):
            day = k
        if response[k]['dt_txt'].endswith("21:00:00"):
            night = k
        k += 1
    temp_day = ''
    temp_night = ''
    result = []
    for days in range(5):
        if day < night:
            temp = str(round(response[day]["main"]["temp"]))
            temp_image = Image.open(
                urlopen(f'http://openweathermap.org/img/wn/{response[day]["weather"][0]["icon"]}.png'))
            temp_day = temp_day + ' // ' + temp + ' °C'
            if image is None:
                image = temp_image
            else:
                image = splice(image, temp_image)
            day += 8
        else:
            temp_day = temp_day + ' // ' + '--'
        temp = str(round(response[night]["main"]["temp"]))
        temp_night = temp_night + ' // ' + temp + ' °C'
        if image is None:
            temp_image = Image.open(
                urlopen(f'http://openweathermap.org/img/wn/{response[night]["weather"][0]["icon"]}.png'))
            image = temp_image
        night += 8
    result.append(temp_day + ' / День\n' + temp_night + ' / Ночь')
    result.append(image)
    return result


def main():
    global schedules, users, lecturers, week_days
    if exists("./schedules_cache.json"):
        schedules = json.load(open("schedules_cache.json", "r"))
    else:
        schedules = {'link': [1, 1, 1], 'groups': {}}
    if exists("./users_cache.json"):
        users = json.load(open("users_cache.json", "r"))
    if exists("./lecturers_cache.json"):
        lecturers = json.load(open("lecturers_cache.json", "r"))
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
                send_message(vk_session, event.user_id, get_random_id(), message='Привет, ' +
                            vk.users.get(user_id=event.user_id)[0]['first_name'] +
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
                send_message(vk_session, event.user_id, get_random_id(), message='Выбери возможность', keyboard=keyboard)

            elif response == 'преподаватель':
                send_message(vk_session, event.user_id, get_random_id(), message='Введите фамилию')
                find_lecturer(longpoll, vk_session, event.user_id)
                response = 'Продолжить'
                keyboard = menu(response)

            elif response == 'погода':
                menu_weather(longpoll, vk_session, event.user_id)
                response = 'Продолжить'
                keyboard = menu(response)

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
                send_message(vk_session, event.user_id, get_random_id(), message='Что хочешь посмотреть?', keyboard=keyboard)


if __name__ == '__main__':
    main()
