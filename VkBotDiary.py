from datetime import datetime
from os import chdir
from sys import exit
from threading import Thread, enumerate as threads
from time import sleep
from traceback import print_exc

from colorama import Fore, Style
from vk_api import VkApi
from vk_api.exceptions import BadPassword, ApiError
from vk_api.longpoll import VkLongPoll, VkEventType

from InitConfig import Config
from InitDatabase import InitDatabase
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days, Subjects, Users_groups, Users_tasks, Lesson_start_end, Users_communities
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
    InitSQL.get_DB().create_tables([Weeks, Days, Subjects, Users_groups,
                                    Users_tasks, Lesson_start_end, Users_communities])


def checking_schedule_on_changes() -> None:
    """Проверка расписания на изменения с заданным периодом ожидания"""
    while True:
        all_files_downloaded = True
        if Config.get_weeks_info()["start_week"] <= datetime.now() <= Config.get_weeks_info()["pre_exam_week"]:
            print(Fore.MAGENTA + "Начинаем парсинг файлов расписания..." + Style.RESET_ALL)
            all_files_downloaded = Parser.download_schedules()
            print(Fore.MAGENTA + "Парсинг файлов расписания завершён!" + Style.RESET_ALL)
        else:
            print(Fore.MAGENTA + "Парсинг файлов расписания не произведён, т. к. семестр ещё не начался/уже закончился!"
                  + Style.RESET_ALL)
        sleep(Config.get_await_time() if all_files_downloaded else 60)


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
    ensure_tables_created()
    print(Fore.BLUE + "Соединение с базой данных установлено!" + Style.RESET_ALL)
    if Config.get_init_database():
        InitDatabase.ensure_start_data_added()
    if "checking_schedule_on_changes" not in [i.name for i in threads()]:
        thread_1 = Thread(target=checking_schedule_on_changes, name="checking_schedule_on_changes")
        thread_1.daemon = True
        print(Fore.CYAN + "Бот запустил поток проверки расписания!" + Style.RESET_ALL)
        thread_1.start()
    vk_session_user = None
    if Config.get_user_info():
        chdir(Config.get_dir_name())
        login, password = Config.get_user_info()
        try:
            vk_session_user = VkApi(login, password)
            vk_session_user.auth()
        except BadPassword:
            vk_session_user = None
            print(Fore.RED + "Ошибка! Логин и/или пароль пользователя для бота введены не правильно! "
                             "Функции подкоманд 'Мем' не будут работать!" + Style.RESET_ALL)
        chdir("..")
        print(Fore.BLUE + "Пользователь для бота авторизировался!" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "Логин и/или пароль пользователя для бота не введены. Функции подкоманд 'Мем' не доступны!"
              + Style.RESET_ALL)

    print(Fore.LIGHTMAGENTA_EX + "Бот начал слушать сообщения!" + Style.RESET_ALL)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and (
                event.text or "attach1_kind" in event.attachments) and event.to_me:
            user_message = event.text
            if "attach1_kind" in event.attachments and event.attachments["attach1_kind"] == 'audiomsg':
                attachs = eval(event.attachments["attachments"])
                try:
                    user_message = SpeechRecognizer.get_phrase(attachs[0]['audio_message']['link_mp3']).lower()
                except ValueError:
                    user_message = "ошибка при обработке звукового сообщения"
            bot = VkBotChat(vk_session, event.user_id, vk_session_user)
            try:
                bot.get_response(user_message)
            except BaseException:
                bot.get_response(None)
                print_exc()
                exit()


if __name__ == '__main__':
    main()
