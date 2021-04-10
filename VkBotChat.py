from io import BytesIO
from re import search, findall
from re import split as re_split
from random import randint, choice

from requests import get as req_get
from vk_api import VkUpload, VkApi
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard
from peewee import DoesNotExist

from VkBotFunctions import VkBotFunctions
from VkBotStatus import States, VkBotStatus
from MySQLStorage import Users, Weeks


class VkBotChat:
    """Класс VkBotChat используется для обработки и отправки сообщений в вк.

    Parameters
    ----------
    vk_session : VkApi
        авторизованное сообщество
    user_id : int
        id пользователя
    vk_session_user : VkApi
        пользователь для отправки мемов
    """

    def __init__(self, vk_session, user_id, vk_session_user):
        self._vk_session = vk_session
        self._user_id = user_id
        self._functions = VkBotFunctions(user_id)
        self._vk_session_user = vk_session_user
        self._flag = True

    def get_response(self, user_message):
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        """
        if VkBotStatus.get_state(self._user_id) != States.NONE:
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
                    self._flag = False
                    keyboard = self._functions.create_menu("клавиатура--отмена")
                    self.send_message(message="Ссылки на сообщество" +
                                              (' или его номера' if VkBotStatus.get_state(
                                                  self._user_id) == States.DELETE_COMMUNITY else '') +
                                              " не найдено!", keyboard=keyboard)
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
                    except BaseException:
                        self._flag = False
                        keyboard = self._functions.create_menu("клавиатура--отмена")
                        if len(communities_names) == 1:
                            self.send_message(message="Неправильно указана ссылка на сообщество!", keyboard=keyboard)
                        else:
                            self.send_message(message="Неправильно указаны ссылки на сообщества!", keyboard=keyboard)
        else:
            if user_message == 'начать':
                self.send_message(message='Привет, чтобы открыть все возможности бота напиши свою группу'
                                          '\nФорма записи группы: ИКБО-03-19')

            elif search(r'([а-я]{4}-\d{2}-\d{2})', user_message):
                if len([i for i in Weeks.select().where(Weeks.group == user_message.upper()).execute()]) > 0:
                    if len([i for i in Users.select().where(Users.user_id == self._user_id).execute()]) != 0:
                        Users.update(group=user_message.upper()).where(Users.user_id == self._user_id).execute()
                    else:
                        Users.create(user_id=self._user_id, group=user_message.upper())
                    self.send_message(
                        message='Группа сохранена! Номер твоей группы: ' + user_message.upper())
                else:
                    self.send_message(message='Такой группы нет, попробуй еще раз.')

            elif user_message == 'расписание':
                self._flag = False
                keyboard = self._functions.create_menu(user_message)
                self.send_message(message='Выбери возможность', keyboard=keyboard)

            elif search(r'(на [а-я]+( [а-я]+)?)|(какая [а-я]{6})', user_message):
                try:
                    group = Users.get(Users.user_id == self._user_id).group  # Для единичной выцепки
                    # group = [i for i in Users.select().where(Users.user_id == self._user_id).limit(1)][0].group  # Для множественной
                    self.send_message(self._functions.schedule_menu(user_message, group))
                except DoesNotExist:  # and IndexError
                    self.send_message(message='Вы не ввели группу.\n Формат ввода: ИКБО-03-19')
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
                        except BaseException:
                            self.send_pic(
                                "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                                "Ошибка vk:  Что-то пошло не так")
                    else:
                        self.send_message("Я бы мог рассказать что-то, но мне лень. ( ͡° ͜ʖ ͡°)")

            elif user_message == 'добавить сообщество':
                self._flag = False
                VkBotStatus.set_state(self._user_id, States.ADD_COMMUNITY)
                keyboard = self._functions.create_menu("клавиатура--отмена")
                self.send_message(message=f"{choice(['Слушаю', 'Внимаю', 'У аппарата'])}... ( ͡° ͜ʖ ͡°)",
                                  keyboard=keyboard)

            elif user_message == 'удалить сообщество':
                comm_from_me, list_comm_urls = self._functions.show_users_communities(self._vk_session_user,
                                                                                      show_name=True, show_url=True)
                if comm_from_me:
                    bot_message = "\nТекущие сообщества:\n" + \
                                  "\n".join([f"{str(i + 1)}) {list_comm_urls[i]}" for i in range(len(list_comm_urls))])
                    self._flag = False
                    VkBotStatus.set_state(self._user_id, States.DELETE_COMMUNITY)
                    keyboard = self._functions.create_menu("клавиатура--отмена", len(list_comm_urls))
                    self.send_message(message=f"{choice(['Слушаю', 'Внимаю', 'У аппарата'])}... ( ͡° ͜ʖ ͡°)" +
                                              bot_message,
                                      keyboard=keyboard)
                else:
                    self.send_message("У вас нет сообществ!")

            elif user_message == 'мои сообщества':
                comm_from_me, list_comm = self._functions.show_users_communities(self._vk_session_user, show_name=True)
                bot_message = ""
                if not comm_from_me:
                    bot_message += "У вас не добавлено ни одного сообщества. Используются дефолтные сообщества бота:"
                self.send_message((bot_message + "\n" if bot_message else "") +
                                  "\n".join([f"{str(i + 1)}) {list_comm[i]}" for i in range(len(list_comm))]))

            else:
                self.send_message(message='Я не знаю такой команды')

        if self._flag:
            keyboard = self._functions.create_menu("Продолжить")
            self.send_message(message='Что хочешь посмотреть?', keyboard=keyboard)

    def send_message(self, message=None, keyboard=None):
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        message : str
            сообщение для пользователя (по умолчанию None)
        keyboard : VkKeyboard
            клавиатура доступная пользователю (по умолчанию None)
        """
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), 'keyboard': keyboard})

    def send_pic(self, image_url, message=None):
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        image_url : str
            ссылка на изображение
        message : str
            сообщение для пользователя (по умолчанию None)
        """
        arr = BytesIO(req_get(image_url).content)
        arr.seek(0)
        upload = VkUpload(self._vk_session)
        photo = upload.photo_messages(arr)
        image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), "attachment": image})
