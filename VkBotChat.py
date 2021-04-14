from io import BytesIO
from re import search, findall
from re import split as re_split
from random import randint, choice

from requests import get as req_get
from vk_api import VkUpload, VkApi
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard
from vk_api.exceptions import ApiError
from peewee import DoesNotExist
from datetime import datetime
from dateparser import parse as date_parse

from VkBotFunctions import VkBotFunctions
from VkBotStatus import States, VkBotStatus
from MySQLStorage import Users_groups, Weeks, Users_tasks
from VkBotParser import Parser


class VkBotChat:
    """Класс VkBotChat используется для обработки и отправки сообщений в вк.

    Parameters
    ----------
    vk_session: VkApi
        авторизованное сообщество
    user_id: int
        id пользователя
    vk_session_user: VkApi
        пользователь для отправки мемов
    """

    def __init__(self, vk_session, user_id, vk_session_user):
        self._vk_session = vk_session
        self._user_id = user_id
        self._functions = VkBotFunctions(user_id)
        self._vk_session_user = vk_session_user
        self._flag = True

    def get_response(self, user_message) -> None:
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        user_message: str
            сообщение пользователя
        """
        if VkBotStatus.get_state(self._user_id) == States.ADD_COMMUNITY or \
                VkBotStatus.get_state(self._user_id) == States.DELETE_COMMUNITY:
            user_message = user_message.lower()
            self._handle_add_delete_community(user_message)
        elif VkBotStatus.get_state(self._user_id) != States.ADD_COMMUNITY and \
                VkBotStatus.get_state(self._user_id) != States.DELETE_COMMUNITY and \
                VkBotStatus.get_state(self._user_id) != States.NONE:
            self._handle_add_delete_change_task(user_message)
        else:
            user_message = user_message.lower()
            if user_message == 'начать':
                self.send_message(message='Привет, чтобы открыть все возможности бота напиши свою группу'
                                          '\nФорма записи группы: ИКБО-03-19.')

            elif search(r'([а-я]{4}-\d{2}-\d{2})', user_message):
                if len([i for i in Weeks.select().where(Weeks.group == user_message.upper()).execute()]) > 0:
                    if len([i for i in
                            Users_groups.select().where(Users_groups.user_id == self._user_id).execute()]) != 0:
                        Users_groups.update(group=user_message.upper()).where(
                            Users_groups.user_id == self._user_id).execute()
                    else:
                        Users_groups.create(user_id=self._user_id, group=user_message.upper())
                    self.send_message(
                        message='Группа сохранена! Номер твоей группы: ' + user_message.upper())
                else:
                    self.send_message(message='Такой группы нет, попробуй еще раз.')

            elif user_message == 'расписание':
                self._flag = False
                keyboard = self._functions.create_menu(user_message)
                self.send_message(message='Выбери возможность', keyboard=keyboard)

            elif search(r'(на [а-я]+( [а-я]+)?)|(какая [а-я]{6})', user_message):
                if Parser.get_bot_parsing_state() and search(r'(на [а-я]+( [а-я]+)?)', user_message):
                    self.send_message(message='Бот обновляет расписание и данная команда временно не доступна.' +
                                              ' Попробуйте позже.')
                else:
                    try:
                        group = Users_groups.get(Users_groups.user_id == self._user_id).group
                        self.send_message(self._functions.schedule_menu(user_message, group))
                    except DoesNotExist:
                        self.send_message(message='Вы не ввели группу.\n Формат ввода: ИКБО-03-19.')

            elif user_message == 'задачи':
                self._flag = False
                keyboard = self._functions.create_menu(user_message)
                self.send_message(message='Выбери возможность', keyboard=keyboard)

            elif user_message == 'добавить задачу':
                bot_message = "Формат даты ввода для задачи с какого и по какое время:\n" + \
                              "'1 января 1970 года 01:00 - 02:24' или 'завтра 12:10 - 14:40'"
                VkBotStatus.set_state(self._user_id, States.ADD_TASK_INIT)
                self._create_cancel_menu(message=bot_message, add_to_existing=True)

            elif user_message == 'удалить задачу':
                VkBotStatus.set_state(self._user_id, States.DELETE_TASK_INIT)
                self._create_cancel_menu(message="Введите дату начала удаляемой задачи", add_to_existing=True)

            elif user_message == 'изменить задачу':
                VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_INIT)
                self._create_cancel_menu(message="Введите дату начала изменяемой задачи", add_to_existing=True)

            elif user_message == 'мем':
                self._flag = False
                keyboard = self._functions.create_menu(user_message)
                self.send_message(message='Выбери возможность', keyboard=keyboard)

            elif user_message == 'случайный мем':
                if self._vk_session_user is None:
                    self.send_pic(
                        "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                        "Ошибка vk:  Не введён логин и пароль пользователя")
                else:
                    if bool(randint(0, 3)):
                        try:
                            photo_url, bot_message = self._functions.send_meme(self._vk_session_user)
                            self.send_pic(photo_url, bot_message)
                        except ApiError:
                            self.send_pic(
                                "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                                "Ошибка vk:  Что-то пошло не так")
                    else:
                        self.send_message("Я бы мог рассказать что-то, но мне лень. ( ͡° ͜ʖ ͡°)")

            elif user_message == 'добавить сообщество':
                if self._vk_session_user is None:
                    self.send_pic(
                        "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                        "Ошибка vk:  Не введён логин и пароль пользователя")
                else:
                    VkBotStatus.set_state(self._user_id, States.ADD_COMMUNITY)
                    self._create_cancel_menu(add_to_existing=True)

            elif user_message == 'удалить сообщество':
                if self._vk_session_user is None:
                    self.send_pic(
                        "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                        "Ошибка vk:  Не введён логин и пароль пользователя")
                else:
                    comm_from_me, list_comm_urls = self._functions.show_users_communities(self._vk_session_user,
                                                                                          show_name=True, show_url=True)
                    if comm_from_me:
                        bot_message = "\nТекущие сообщества:\n" + \
                                      "\n".join(
                                          [f"{str(i + 1)}) {list_comm_urls[i]}" for i in range(len(list_comm_urls))])
                        VkBotStatus.set_state(self._user_id, States.DELETE_COMMUNITY)
                        self._create_cancel_menu(message=bot_message, buttons=len(list_comm_urls), add_to_existing=True)
                    else:
                        self.send_message("У вас нет сообществ!")

            elif user_message == 'мои сообщества':
                if self._vk_session_user is None:
                    self.send_pic(
                        "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                        "Ошибка vk:  Не введён логин и пароль пользователя")
                else:
                    comm_from_me, list_comm = self._functions.show_users_communities(self._vk_session_user,
                                                                                     show_name=True)
                    bot_message = ""
                    if not comm_from_me:
                        bot_message += "У вас не добавлено ни одного сообщества. " \
                                       "Используются дефолтные сообщества бота:"
                    self.send_message((bot_message + "\n" if bot_message else "") +
                                      "\n".join([f"{str(i + 1)}) {list_comm[i]}" for i in range(len(list_comm))]))

            else:
                self.send_message(message='Я не знаю такой команды.')

        if self._flag:
            keyboard = self._functions.create_menu("Продолжить")
            self.send_message(message='Что хочешь посмотреть?', keyboard=keyboard)

    def send_message(self, message=None, keyboard=None) -> None:
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        message: str
            сообщение для пользователя (по умолчанию None)
        keyboard: VkKeyboard
            клавиатура доступная пользователю (по умолчанию None)
        """
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), 'keyboard': keyboard})

    def send_pic(self, image_url, message=None) -> None:
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        image_url: str
            ссылка на изображение
        message: str
            сообщение для пользователя (по умолчанию None)
        """
        arr = BytesIO(req_get(image_url).content)
        arr.seek(0)
        upload = VkUpload(self._vk_session)
        photo = upload.photo_messages(arr)
        image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), "attachment": image})

    def _create_cancel_menu(self, message="", add_to_existing=False, buttons=0, list_of_named_buttons=None) -> None:
        """Создаёт меню "Отмена"

        Parameters
        ----------
        message: str
            текст для добавления к стандартному сообщению
        add_to_existing: bool
            добавить к стандартному сообщению или вывести только текст из 'message'
        buttons: int
            количество номерных кнопок
        list_of_named_buttons: list
            список названий для кнопок
        """
        self._flag = False
        result_message = f"{choice(['Слушаю', 'Внимаю', 'У аппарата'])}... ( ͡° ͜ʖ ͡°)\n{message}" \
            if add_to_existing else message
        keyboard = self._functions.create_menu("клавиатура--отмена", buttons, list_of_named_buttons)
        self.send_message(message=result_message.strip(), keyboard=keyboard)

    def _handle_add_delete_community(self, user_message: str) -> None:
        """Обрабатывает запрос пользователя на добавление или удаление сообщества или сообществ.

        Parameters
        ----------
        user_message: str
            сообщение пользователя
        """
        if user_message == 'отмена':
            VkBotStatus.set_state(self._user_id, States.NONE)
            self.send_message(f"Бот больше не {choice(['cлушает', 'внимает'])}... ಠ╭╮ಠ")
        else:
            communities_links = [i.strip() for i in re_split(', | |\n', user_message)]

            communities_names = []
            for i in communities_links:
                if search(r'(?:(?:https?|ftp|http?)://)?[\w/\-?=%.]+\.[\w/\-&?=%.]+', i):
                    communities_names.append(str(findall(r'(?:(?:https?|ftp|http?)://)?[\w/\-?=%.]+\.[\w/\-&?=%.]+',
                                                         i)[0]).split("/")[-1])
            communities_numbers = []
            if VkBotStatus.get_state(self._user_id) == States.DELETE_COMMUNITY and len(communities_names) == 0:
                for i in communities_links:
                    try:
                        if int(i) - 1 >= 0:
                            communities_numbers.append(int(i) - 1)
                    except ValueError:
                        pass
                if len(communities_numbers) != 0:
                    comm_from_me, list_comm_urls = self._functions.show_users_communities(self._vk_session_user,
                                                                                          show_url=True)
                    if comm_from_me:
                        for i in communities_numbers:
                            if i < len(list_comm_urls):
                                communities_names.append(list_comm_urls[i].split("/")[-1])

            if len(communities_names) == 0 and len(communities_numbers) == 0:
                self._create_cancel_menu(message="Ссылки на сообщество" +
                                                 (' или его номера' if VkBotStatus.get_state(
                                                     self._user_id) == States.DELETE_COMMUNITY else '') +
                                                 " не найдено!")
            else:
                try:
                    result = self._functions.change_users_community(self._vk_session_user,
                                                                    VkBotStatus.get_state(
                                                                        self._user_id) == States.DELETE_COMMUNITY,
                                                                    communities_names)
                    VkBotStatus.set_state(self._user_id, States.NONE)
                    if len(communities_names) == 1:
                        self.send_message(message=f"Сообщество {'удалено' if result else 'сохранено'}!")
                    else:
                        self.send_message(message=f"Сообщества {'удалены' if result else 'сохранены'}!")
                except ApiError:
                    if len(communities_names) == 1:
                        bot_message = "Неправильно указана ссылка на сообщество!"
                    else:
                        bot_message = "Неправильно указаны ссылки на сообщества!"
                    self._create_cancel_menu(message=bot_message)

    def _handle_add_delete_change_task(self, user_message: str) -> None:
        """Обрабатывает запрос пользователя на добавление, удаление или изменение задачи или задач.

        Parameters
        ----------
        user_message: str
            сообщение пользователя
        """
        if user_message.lower() == 'отмена':
            VkBotStatus.set_state(self._user_id, States.NONE)
            self.send_message(f"Бот больше не {choice(['cлушает', 'внимает'])}... ಠ╭╮ಠ")
        else:
            if VkBotStatus.get_state(self._user_id) == States.ADD_TASK_INIT or \
                    VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_ENTER_TIME:
                try:
                    if '-' not in user_message:
                        raise ValueError
                    dates = [date_parse(i.strip()) for i in user_message.split("-")]
                    if any([i is None for i in dates]):
                        raise ValueError
                    dates[1] = datetime.combine(dates[0], dates[1].time())

                    existing_tasks = [i for i in Users_tasks.select().where((Users_tasks.user_id == self._user_id) &
                                                                            (((Users_tasks.start_date < dates[0]) &
                                                                              (Users_tasks.end_date > dates[0])) |
                                                                             ((Users_tasks.start_date < dates[1]) &
                                                                              (Users_tasks.end_date > dates[1])) |
                                                                             ((Users_tasks.start_date > dates[0]) &
                                                                              (Users_tasks.end_date > dates[0]) &
                                                                              (Users_tasks.start_date < dates[1]) &
                                                                              (Users_tasks.end_date < dates[1]))))
                        .execute()]

                    if len(existing_tasks) == 0:
                        if VkBotStatus.get_state(self._user_id) == States.ADD_TASK_INIT:
                            VkBotStatus.set_state(self._user_id, States.ADD_TASK_HAS_DATE, dates)
                        else:
                            VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_ENTER_DATA,
                                                  [VkBotStatus.get_data(self._user_id), dates])
                        self.send_message("Период задачи поставлен на дату " + dates[0].strftime('%d.%m.%Y с %H:%M') +
                                          dates[1].strftime(' по %H:%M'))
                        self._create_cancel_menu(message="Введите задачу...")
                    else:
                        existing_tasks.sort(key=lambda x: x.start_date.time())
                        bot_message = "\n".join([f"{i + 1}) {existing_tasks[i].start_date.time().strftime('%H:%M')} "
                                                 f"- {existing_tasks[i].end_date.time().strftime('%H:%M')}: "
                                                 f"{existing_tasks[i].task}"
                                                 for i in range(len(existing_tasks))])
                        self._create_cancel_menu(
                            message=f"На указанной дате уже есть задач{'а' if len(existing_tasks) == 1 else 'и'}. "
                                    f"{'Какую дату' if len(existing_tasks) == 1 else 'Какие даты'} задачи "
                                    "хотите удалить? Вводить дату начала задачи или задач. "
                                    f"Для отмены введите 'Отмена'\n{bot_message}",
                            buttons=len(existing_tasks),
                            list_of_named_buttons=[i.start_date.time().strftime('%H:%M') for i in existing_tasks])
                        VkBotStatus.set_state(self._user_id, States.DELETE_TASK_HAS_DATE, dates[0])
                except ValueError:
                    self._create_cancel_menu(
                        message="Дата указана неверно, бот не смог её распарсить. Попробуйте ещё раз.")
            elif VkBotStatus.get_state(self._user_id) == States.ADD_TASK_HAS_DATE or \
                    VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_ENTER_DATA:
                dates = VkBotStatus.get_data(self._user_id)
                if len(user_message.strip()) != 0:
                    if VkBotStatus.get_state(self._user_id) == States.ADD_TASK_HAS_DATE:
                        Users_tasks.create(user_id=self._user_id,
                                           start_date=dates[0],
                                           end_date=dates[1],
                                           task=user_message.strip())
                        self.send_message(message="Задача сохранена!")
                    else:
                        if isinstance(VkBotStatus.get_data(self._user_id), list):
                            date_to_update = Users_tasks.get((Users_tasks.user_id == self._user_id) &
                                                             (Users_tasks.start_date == dates[0]))
                            date_to_update.start_date = VkBotStatus.get_data(self._user_id)[1][0]
                            date_to_update.end_date = VkBotStatus.get_data(self._user_id)[1][1]
                        else:
                            date_to_update = Users_tasks.get((Users_tasks.user_id == self._user_id) &
                                                             (Users_tasks.start_date == dates))
                        date_to_update.task = user_message.strip()
                        date_to_update.save()
                        self.send_message(message="Задача обновлена!")
                    VkBotStatus.set_state(self._user_id, States.NONE)
                else:
                    self._create_cancel_menu(
                        message="Задачу не удалось сохранить, так как пользователь ничего не ввёл." +
                                " Введите задачу ещё раз.")
            elif VkBotStatus.get_state(self._user_id) == States.DELETE_TASK_INIT or \
                    VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_INIT:
                try:
                    date = date_parse(user_message.strip())
                    if date is None:
                        raise ValueError
                    if VkBotStatus.get_state(self._user_id) == States.DELETE_TASK_INIT:
                        VkBotStatus.set_state(self._user_id, States.DELETE_TASK_HAS_DATE, date)
                    else:
                        VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_HAS_DATE, date)

                    min_date = datetime.combine(date.date(), datetime.min.time())
                    max_date = datetime.combine(date.date(), datetime.max.time())

                    dates = [i for i in Users_tasks.select().where((Users_tasks.user_id == self._user_id) &
                                                                   (Users_tasks.start_date >= min_date) &
                                                                   (Users_tasks.start_date <= max_date)).execute()]
                    if len(dates) == 0:
                        self.send_message(message="Задач на эту дату не существует.")
                    else:
                        dates.sort(key=lambda x: x.start_date.time())
                        list_of_tasks = "\n".join([f"{i + 1}) {dates[i].start_date.time().strftime('%H:%M')} "
                                                   f"- {dates[i].end_date.time().strftime('%H:%M')}: {dates[i].task}"
                                                   for i in range(len(dates))])
                        self._create_cancel_menu(message=f"Введите дату начала задачи или задач...\n{list_of_tasks}",
                                                 buttons=len(dates),
                                                 list_of_named_buttons=[i.start_date.time().strftime('%H:%M')
                                                                        for i in dates])
                except ValueError:
                    self._create_cancel_menu(
                        message="Дата указана неверно, бот не смог её распарсить. Попробуйте ещё раз.")
            elif VkBotStatus.get_state(self._user_id) == States.DELETE_TASK_HAS_DATE or \
                    VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_HAS_DATE:
                date = VkBotStatus.get_data(self._user_id).date()
                if len(user_message.strip()) != 0:
                    user_dates = [i.strip() for i in re_split(', | |\n', user_message)]
                    parsed_user_dates = []
                    for i in user_dates:
                        if search(r'[0-9]{1,2}:[0-9]{1,2}', i):
                            parsed_date = date_parse(str(findall(r'[0-9]{1,2}:[0-9]{1,2}', i)[0]))
                            if parsed_date is not None:
                                parsed_user_dates.append(parsed_date.time())
                            if VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_HAS_DATE and \
                                    len(parsed_user_dates) > 0:
                                break
                    if len(parsed_user_dates) > 0:
                        parsed_user_dates = [datetime.combine(date, i) for i in parsed_user_dates]
                        if VkBotStatus.get_state(self._user_id) == States.DELETE_TASK_HAS_DATE:
                            Users_tasks.delete().where((Users_tasks.user_id == self._user_id) &
                                                       (Users_tasks.start_date << parsed_user_dates)).execute()
                        else:
                            self._create_cancel_menu(message="Что вы хотите изменить в задаче?"
                                                             "\n1) Всю задачу время начала и конца и текст задачи"
                                                             "\n2) Только текст задачи",
                                                     buttons=2)
                            VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_CHOOSE, parsed_user_dates[0])
                            return
                    else:
                        self._create_cancel_menu(
                            message="Задачу или задачи не удалось " +
                                    ('удалить' if VkBotStatus.get_state(self._user_id) ==
                                                  States.DELETE_TASK_HAS_DATE else 'изменить') +
                                    ", так как пользователь ввёл неправильную дату."
                                    + "Пример: 12:12 Введите дату или даты ещё раз.")
                else:
                    self._create_cancel_menu(
                        message="Задачу или задачи не удалось " +
                                ('удалить' if VkBotStatus.get_state(self._user_id) ==
                                              States.DELETE_TASK_HAS_DATE else 'изменить') +
                                ", так как пользователь ничего не ввёл." +
                                " Введите дату или даты ещё раз.")
                VkBotStatus.set_state(self._user_id, States.NONE)
            elif VkBotStatus.get_state(self._user_id) == States.CHANGE_TASK_CHOOSE:
                try:
                    if int(user_message) == 1:
                        bot_message = "Формат даты ввода для задачи с какого и по какое время:\n" + \
                                      "'1 января 1970 года 01:00 - 02:24' или 'завтра 12:10 - 14:40'"
                        VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_ENTER_TIME,
                                              VkBotStatus.get_data(self._user_id))
                        self._create_cancel_menu(message=bot_message)
                    elif int(user_message) == 2:
                        self._create_cancel_menu(message="Введите задачу...")
                        VkBotStatus.set_state(self._user_id, States.CHANGE_TASK_ENTER_DATA,
                                              VkBotStatus.get_data(self._user_id))
                    else:
                        self._create_cancel_menu(message="Такой цифры нет в списке!", buttons=2)
                except ValueError:
                    self._create_cancel_menu(message="Неправильный ввод, выберите из списка вариант!", buttons=2)
