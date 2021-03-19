from os import chdir

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from Init_config import Config
from Bot_parser import Parser
from VkBotChat import VkBotChat


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

def main():
    config = Config()
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
