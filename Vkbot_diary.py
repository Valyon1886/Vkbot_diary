import os
import re
import json
from os.path import exists
from Init_config import Config

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from Bot_parser import Parser
from VkBot import VkBot

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

# TODO:
#  Почистить код
#  Сделать конф файл - сделан конфиг для токена, но думаю туда ещё надо будет добавить другие параметры
#  Переписать по классам

schedules = dict()
users = dict()
week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
parser = Parser()
bot = VkBot()
if not exists("local_files"):
    os.makedirs("local_files")
config = Config()

if exists("./schedules_cache.json"):
    schedules = json.load(open("schedules_cache.json", "r"))
else:
    schedules = {'link': [1 for _ in range(4)], 'groups': {}}
if exists("./local_files/users_cache.json"):
    users = json.load(open("local_files/users_cache.json", "r"))
parser.schedule(schedules)

vk_session = vk_api.VkApi(token=config.get_token())
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
        response = event.text.lower()
        keyboard = bot.menu(response)

        if response == 'начать':
            bot.send_message(vk_session, event.user_id, get_random_id(),
                         message='Привет, ' + vk.users.get(user_id=event.user_id)[0]['first_name'] +
                                 '\nНапиши свою группу\nФорма записи группы: ИКБО-09-19')
            response = 'Продолжить'
            keyboard = bot.menu(response)

        elif re.search(r'([а-я]{2}бо-\d{2}-\d{2})', response):
            if response.upper() in schedules["groups"]:
                users[str(event.user_id)] = response.upper()
                json.dump(users, open("local_files/users_cache.json", "w"))
                bot.send_message(vk_session, event.user_id, get_random_id(),
                             message='Группа сохранена! Номер твоей группы: ' + users[str(event.user_id)])
            else:
                bot.send_message(vk_session, event.user_id, get_random_id(),
                             message='Такой группы нет, попробуй еще раз.')
            response = 'Продолжить'
            keyboard = bot.menu(response)

        elif response == 'расписание':
            bot.send_message(vk_session, event.user_id, get_random_id(), message='Выбери возможность',
                         keyboard=keyboard)

        elif re.search(r'(на [а-я]+( [а-я]+)?)|(какая [а-я]{6})', response):
            try:
                bot.schedule_menu(response, vk_session, event.user_id, get_random_id(), schedules, users)
            except KeyError:
                bot.send_message(vk_session, event.user_id, get_random_id(),
                             message='Вы не ввели группу.\n Формат ввода: ИКБО-09-19')
            response = 'Продолжить'
            keyboard = bot.menu(response)

        else:
            bot.send_message(vk_session, event.user_id, get_random_id(), message='Я не знаю такой команды')
            response = 'Продолжить'
            keyboard = bot.menu(response)

        if response == 'Продолжить':
            bot.send_message(vk_session, event.user_id, get_random_id(), message='Что хочешь посмотреть?',
                         keyboard=keyboard)
