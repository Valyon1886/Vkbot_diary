from contextlib import suppress
from datetime import datetime
from json import loads
from os import chdir
from sys import exit
from threading import Thread, enumerate as threads
from time import sleep
from traceback import print_exc
from typing import List

from colorama import Fore, Style
from vk_api import VkApi
from vk_api.exceptions import BadPassword, ApiError, Captcha
from vk_api.longpoll import VkLongPoll, VkEventType

from InitConfig import Config
from InitDatabase import InitDatabase
from InitSQL import InitSQL
from MySQLStorage import (
    Weeks, Days, Subjects, Users_groups, Users_tasks, Lesson_start_end, Users_communities, Groups, ExamDays, Disciplines
)
from SpeechRecognizer import SpeechRecognizer
from VkBotChat import VkBotChat
from VkBotParser import Parser


# TODO:
#  1. Расписание (реализовано) ✓
#  2. Пользователи/настройки (реализовано) ✓
#  3. Задачи (реализованы) ✓
#  Добавить в ответы бота смайлики, Серёге надо)
#  Вывод расписания в виде картинки

def ensure_tables_created() -> None:
    """Проверка, что таблицы созданы"""
    InitSQL.get_DB().create_tables([Groups, Weeks, Days, Subjects, ExamDays, Disciplines, Users_groups,
                                    Users_tasks, Lesson_start_end, Users_communities])


def checking_schedule_on_changes() -> None:
    """Проверка расписания на изменения с заданным периодом ожидания"""
    sleep(0.1)
    while True:
        all_files_parsed = True
        if Config.get_weeks_info()["start_week"] <= datetime.now() <= Config.get_weeks_info()["pre_exam_week"]:
            print(Fore.MAGENTA + "Начинаем парсинг файлов расписания..." + Style.RESET_ALL)
            try:
                all_files_parsed = Parser.download_schedules()
                print(Fore.MAGENTA + "Парсинг файлов расписания завершён!" + Style.RESET_ALL)
            except BaseException:
                print(
                    Fore.LIGHTRED_EX + "Парсинг файлов расписания прерван ошибкой! Перезапускаем через некоторое время!"
                    + Style.RESET_ALL
                )
                print_exc()
                all_files_parsed = False
        else:
            print(Fore.MAGENTA + "Парсинг файлов расписания не произведён, т. к. семестр ещё не начался/уже закончился!"
                  + Style.RESET_ALL)
        sleep(Config.get_await_time() if all_files_parsed else 300)


def parse_unanswered_messages(vk_session: VkApi) -> List[dict]:
    """Парсит все неотвеченные сообщения

    Parameters
    ----------
    vk_session: VkApi
        сессия бота

    Return
    ----------
    last_messages_list: List[dict]
        список неотвеченных сообщений
    """
    vk = vk_session.get_api()
    conversations = vk.messages.getConversations(count=200, filter="unanswered")
    conversations_items = conversations['items']
    conv_count = conversations['count'] - 200
    offset = 200
    while conv_count > 200:
        conversations_items.extend(vk.messages.getConversations(count=200, filter="unanswered", offset=offset))
        offset += 200
        conv_count -= 200
    return [i['last_message'] for i in conversations_items if i.get("last_message", None) is not None]


def parse_message(vk_session: VkApi, vk_session_user: VkApi, text: str, attachments: List[dict], user_id: int) -> None:
    """Парсит сообщение

    Parameters
    ----------
    vk_session: VkApi
        сессия бота
    vk_session_user: VkApi
        сессия пользователя
    text: str
        текст сообщения
    attachments: List[dict]
        вложения сообщения
    user_id: int
        id пользователя
    """
    user_message = text
    for a in attachments:
        if a["type"] == "audio_message":
            try:
                user_message = SpeechRecognizer.get_phrase(a["audio_message"]["link_mp3"]).lower()
            except ValueError:
                user_message = "ошибка при обработке звукового сообщения"
            break
        elif a["type"] == "sticker":
            user_message = "стикер"
    bot = VkBotChat(vk_session, user_id, vk_session_user)
    try:
        bot.get_response(user_message)
    except BaseException:
        bot.get_response(None)
        print_exc()
        exit()


def main() -> None:
    """Функция запуска бота и прослушивание им сообщений от пользователя"""
    Config.read_config()
    print(Fore.BLUE + "Файл настроек загружен!" + Style.RESET_ALL)
    try:
        vk_session = VkApi(token=Config.get_token())
        longpoll = VkLongPoll(vk_session)
        print(Fore.BLUE + "Бот залогинился!" + Style.RESET_ALL)
    except ApiError:
        exit("Ошибка! Неправильно введён токен для бота! Измените токен бота на правильный!")
        return
    vk_session_user = None
    if Config.get_user_info():
        chdir(Config.get_dir_name())
        login, password = Config.get_user_info()
        captcha = None
        while True:
            try:
                if captcha is not None:
                    raise captcha
                vk_session_user = VkApi(login, password)
                vk_session_user.auth()
                break
            except Captcha as ex:
                try:
                    print(Fore.RED + f"Нужна капча! Пройдите по этой ссылке {ex.get_url()} и решите её!" +
                          Style.RESET_ALL)
                    captcha_solve = input("Введите капчу: ")
                    ex.try_again(captcha_solve)
                except Captcha as ex_c:
                    captcha = ex_c
            except BadPassword:
                vk_session_user = None
                print(Fore.RED + "Ошибка! Логин и/или пароль пользователя для бота введены не правильно! "
                                 "Функции подкоманд 'Мем' не будут работать!" + Style.RESET_ALL)
                break
        chdir("..")
        print(Fore.BLUE + "Пользователь для бота авторизировался!" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "Логин и/или пароль пользователя для бота не введены. Функции подкоманд 'Мем' не доступны!"
              + Style.RESET_ALL)
    ensure_tables_created()
    print(Fore.BLUE + "Соединение с базой данных установлено!" + Style.RESET_ALL)
    if Config.get_init_database():
        InitDatabase.ensure_start_data_added()
    if "checking_schedule_on_changes" not in [i.name for i in threads()]:
        Parser.set_bot_parsed_date(Config.get_last_parsed_date())
        thread_1 = Thread(target=checking_schedule_on_changes, name="checking_schedule_on_changes", daemon=True)
        print(Fore.CYAN + "Бот запустил поток проверки расписания!" + Style.RESET_ALL)
        thread_1.start()

    print(Fore.LIGHTMAGENTA_EX + "Бот начал слушать сообщения!" + Style.RESET_ALL)
    for message in parse_unanswered_messages(vk_session):
        with suppress(ApiError):
            parse_message(vk_session, vk_session_user,
                          text=message["text"], attachments=message.get("attachments", []), user_id=message["from_id"])
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            parse_message(vk_session, vk_session_user,
                          text=event.text, attachments=loads(event.attachments.get("attachments", "[]")),
                          user_id=event.user_id)


if __name__ == '__main__':
    main()
