from requests import get as req_get
import io
from re import search
from random import randint, choice

from vk_api import VkUpload, VkApi
from vk_api.utils import get_random_id

from VkBotFunctions import VkBotFunctions
from vk_api.keyboard import VkKeyboard


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
    
    def get_response(self, user_message, schedule, config):
        """Анализирует запрос пользователя и отвечает на него.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        schedule : dict
            расписание
        config : Config
            конфиг для работы с файлами
        """
        if user_message == 'начать':
            self.send_message(message='Привет, чтобы открыть все возможности бота напиши свою группу'
                                      '\nФорма записи группы: ИКБО-03-19')

        elif search(r'([а-я]{4}-\d{2}-\d{2})', user_message):
            if user_message.upper() in schedule["groups"]:
                config.users_dict[str(self._user_id)] = user_message.upper()
                config.save_users_dict()
                self.send_message(
                    message='Группа сохранена! Номер твоей группы: ' + config.users_dict[str(self._user_id)])
            else:
                self.send_message(message='Такой группы нет, попробуй еще раз.')

        elif user_message == 'расписание':
            keyboard = self._functions.create_menu(user_message)
            self.send_message(message='Выбери возможность', keyboard=keyboard)
            self._flag = False

        elif search(r'(на [а-я]+( [а-я]+)?)|(какая [а-я]{6})', user_message):
            try:
                self.send_message(self._functions.schedule_menu(user_message, schedule, config.users_dict))
            except KeyError:
                self.send_message(message='Вы не ввели группу.\n Формат ввода: ИКБО-03-19')

        elif user_message == 'случайный мем':
            self.send_meme()

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
        message : str
            сообщение для пользователя (по умолчанию None)
        image_url : str
            ссылка на изображение
        """
        arr = io.BytesIO(req_get(image_url).content)
        arr.seek(0)
        upload = VkUpload(self._vk_session)
        photo = upload.photo_messages(arr)
        image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), "attachment": image})

    def send_meme(self):
        """Отправляет пользователю случайный мем."""
        if self._vk_session_user is None:
            self.send_pic("http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                          "Ошибка vk:  Не введён логин и пароль пользователя")
            return
        if bool(randint(0, 3)):
            _300_answers = [
                'Ну, держи!',
                'Ah, shit, here we go again.',
                'Ты сам напросился...',
                'Не следовало тебе меня спрашивать...',
                'Ха-ха-ха-ха.... Извини',
                '( ͡° ͜ʖ ͡°)',
                'Ну что, пацаны, аниме?',
                'Ну чё, народ, погнали, на*уй! Ё***ный в рот!'
            ]
            _300_communities = [
                -45045130,  # - Хрень, какой-то паблик
                -45523862,  # - Томат
                -67580761,  # - КБ
                -57846937,  # - MDK
                -12382740,  # - ЁП
                -45745333,  # - 4ch
                -76628628,  # - Silvername
            ]
            own_id = choice(_300_communities)
            try:
                # Тырим с вк фотки)
                vk_session = self._vk_session_user
                vk = vk_session.get_api()
                photos_count = vk.photos.get(owner_id=own_id, album_id="wall", count=1).get('count')
                photo_sizes = vk.photos.get(owner_id=own_id,
                                            album_id="wall",
                                            count=1,
                                            offset=randint(0, photos_count) - 1).get('items')[0].get('sizes')
                max_photo_height = 0
                photo_url = ""
                for i in photo_sizes:
                    if i.get('height') > max_photo_height:
                        max_photo_height = i.get('height')
                for i in photo_sizes:
                    if i.get('height') == max_photo_height:
                        photo_url = i.get('url')
                        break

                self.send_pic(photo_url, choice(_300_answers))
            except BaseException:
                self.send_pic(
                    "http://cdn.bolshoyvopros.ru/files/users/images/bd/02/bd027e654c2fbb9f100e372dc2156d4d.jpg",
                    "Ошибка vk:  Что-то пошло не так")
        else:
            self.send_message("Я бы мог рассказать что-то, но мне лень. ( ͡° ͜ʖ ͡°)")
