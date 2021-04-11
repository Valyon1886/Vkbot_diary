from os import chdir
from threading import Thread
from time import sleep

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from InitConfig import Config
from VkBotParser import Parser
from VkBotChat import VkBotChat
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days, Subjects, Users_groups, Users_notes, Lesson_start_end, Users_communities
from InitDatabase import InitDatabase
from SpeechRecognizer import SpeechRecognizer


# TODO:
#  1. Расписание (реализовано, обновляется, но надо прикрутить отдельный поток обновления)
#  2. Пользователи/настройки (реализовано)
#  3. Заметки (to be continued)
#  Добавление заметок (напротив предмета, см таблицу)
#  Добавление своих пунктов в расписание (см таблицу)
#  При парсинге расписания и заметок на день сортировать их в порядке возрастания времени начала как
#                                                               в Things to practice/README.md и выводить в виде таблицы
#  Мб ещё прикрутить работу со всеми институтами, это не сложно
#  Разобраться с requests, надо ли добавлять в requirements, не ломает ли установку других зависимостей.

def ensure_tables_created():
    """Проверка, что таблицы созданы"""
    InitSQL.get_DB().create_tables([Weeks, Days, Subjects, Users_groups,
                                    Users_notes, Lesson_start_end, Users_communities])


def checking_schedule_on_changes():
    """Проверка расписания на изменения с заданным периодом ожидания"""
    while True:
        print("Начинаем парсинг файлов расписания...")
        all_files_downloaded = Parser.download_schedules()
        print("Парсинг файлов расписания завершён!")
        sleep(Config.get_await_time() if all_files_downloaded else 60)


def main():
    """Функция запуска бота и прослушивание им сообщений от пользователя"""
    Config.read_config()
    print("Файл настроек загружен!")
    ensure_tables_created()
    print("Соединение с базой данных установлено!")
    if Config.get_init_database():
        InitDatabase.ensure_start_data_added()
    thread_1 = Thread(target=checking_schedule_on_changes)
    print("Бот запустил поток проверки расписания!")
    thread_1.start()
    vk_session = VkApi(token=Config.get_token())
    print("Бот залогинился!")
    vk_session_user = None
    if Config.get_user_info():
        chdir(Config.get_dir_name())
        login, password = Config.get_user_info()
        vk_session_user = VkApi(login, password)
        vk_session_user.auth()
        chdir("..")
        print("Пользователь для бота авторизировался!")
    longpoll = VkLongPoll(vk_session)
    print("Бот начал слушать сообщения!")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and (
                event.text or "attach1_kind" in event.attachments) and event.to_me:
            user_message = event.text.lower()
            if "attach1_kind" in event.attachments and event.attachments["attach1_kind"] == 'audiomsg':
                attachs = eval(event.attachments["attachments"])
                user_message = SpeechRecognizer.get_phrase(attachs[0]['audio_message']['link_mp3']).lower()
            bot = VkBotChat(vk_session, event.user_id, vk_session_user)
            bot.get_response(user_message)


if __name__ == '__main__':
    main()
