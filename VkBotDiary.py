from os import chdir

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from InitConfig import Config
from VkBotParser import Parser
from VkBotChat import VkBotChat
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days, Subjects, Users, Users_notes, Lesson_start_end, Users_communities
from InitDatabase import InitDatabase
from SpeechRecognizer import SpeechRecognizer


# TODO:
#  1 Расписание (реализовано наполовину) 2. Пользователи/настройки (реализовано) 3. Заметки (to be continued)
#  Добавление заметок (напротив предмета, см таблицу)
#  Добавление своих пунктов в расписание (см таблицу)
#  Обновление расписания в бд (с сохранением записей пользователя) !!!!!!!!!!!!!!!!!
#  При парсинге расписания и заметок на день сортировать их в порядке возрастания времени начала как
#                                                               в Things to practice/README.md и выводить в виде таблицы

def ensure_tables_created():
    """Проверка, что таблицы созданы"""
    InitSQL.get_DB().create_tables([Weeks, Days, Subjects, Users,
                                    Users_notes, Lesson_start_end, Users_communities])


def main():
    """Функция запуска бота и прослушивание им сообщений от пользователя"""
    config = Config()
    print("Файл настроек загружен!")
    ensure_tables_created()
    print("Соединение с базой данных установлено!")
    if config.get_init_database():
        InitDatabase.ensure_start_data_added()
    Parser(config)
    vk_session = VkApi(token=config.get_token())
    print("Бот залогинился!")
    vk_session_user = None
    if config.get_user_info():
        chdir(config.get_dir_name())
        login, password = config.get_user_info()
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
