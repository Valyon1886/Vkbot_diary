from os import chdir

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from InitConfig import Config
from BotParser import Parser
from VkBotChat import VkBotChat
from InitSQL import InitSQL
from MySQLStorage import Weeks, Days_Lessons, Schedule_of_subject, Users, Users_notes
from InitDatabase import InitDatabase


# TODO:
#  Отображение расписания с сайта
#  Поддержка голосового ввода
#  Загрузка расписания в бд (после этого можно будет добавлять заметки)
#  1 Расписание 2. Пользователи/настройки 3. Заметки
#  Добавление заметок (напротив предмета, см таблицу)
#  Добавление своих пунктов в расписание (см таблицу)
#  Вывод расписания из бд (на сегодня/на неделю)
#  Обновление расписания в бд (с сохранением записей пользователя) !!!!!!!!!!!!!!!!!
#  Случайный мем - работает с помощью обычного пользователя | надо доделать!
#  Почистить код
#  Сделать конф файл - сделан конфиг для токена, но думаю туда ещё надо будет добавить другие параметры

def ensure_tables_created():
    """Проверка, что таблицы созданы"""
    InitSQL.get_DB().create_tables([Weeks, Days_Lessons, Schedule_of_subject, Users, Users_notes])


def main():
    """Функция запуска бота и прослушивание им сообщений от пользователя"""
    config = Config()
    print("Файл настроек загружен!")
    ensure_tables_created()
    print("Соединение с базой данных установлено!")
    if config.get_init_database():
        InitDatabase.ensure_start_data_added()
    parser = Parser()
    schedule = parser.get_schedules()
    vk_session = VkApi(token=config.get_token())
    vk_session_user = None
    if config.get_user_info():
        chdir(config.get_dir_name())
        login, password = config.get_user_info()
        vk_session_user = VkApi(login, password)
        vk_session_user.auth()
        chdir("..")
    print("Бот залогинился!")
    longpoll = VkLongPoll(vk_session)
    print("Бот начал слушать сообщения!")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            bot = VkBotChat(vk_session, event.user_id, vk_session_user)
            user_message = event.text.lower()
            bot.get_response(user_message, schedule, config)


if __name__ == '__main__':
    main()
