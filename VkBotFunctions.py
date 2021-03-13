from datetime import datetime
from random import randint, choice
from requests import get as req_get
from os import remove

from vk_api import VkUpload
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class VkBotFunctions:
    def __init__(self, vk_session, user_id, vk_session_user):
        self._week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        self._vk_session = vk_session
        self._user_id = user_id
        self._vk_session_user = vk_session_user

    def send_message(self, message=None, keyboard=None):
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), 'keyboard': keyboard})

    def send_pic(self, image_url, message=None):
        image_str = image_url.split("/")[-1].split("?")[0] \
            if '?' in image_url.split("/")[-1] \
            else image_url.split("/")[-1]
        open(image_str, "wb").write(req_get(image_url).content)
        upload = VkUpload(self._vk_session)
        photo = upload.photo_messages(image_str)
        image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
        self._vk_session.method('messages.send', {'user_id': self._user_id, 'message': message,
                                                  'random_id': get_random_id(), "attachment": image})
        remove(image_str)

    @staticmethod
    def create_menu(response):
        keyboard = VkKeyboard(one_time=True)

        if response == 'Продолжить':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Случайный мем')
            keyboard.add_line()
            keyboard.add_button('Добавить задачу', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Изменить задачу', color=VkKeyboardColor.NEGATIVE)

        if response == 'расписание':
            keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Какая неделя?')
            keyboard.add_button('Какая группа?')

        keyboard = keyboard.get_keyboard()
        return keyboard

    def schedule_menu(self, response, schedules, users):
        if response == "на сегодня":
            week_day = datetime.now().isoweekday() - 1
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence = self._make_schedule(week_day, student_group)
                self.send_message(message='Расписание на сегодня:\n' + week_day + '\n' + full_sentence)
            else:
                self.send_message(message='Выходной')
        if response == "на завтра":
            week_day = datetime.now().isoweekday()
            if week_day == 7:
                week_day = 0
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence = self._make_schedule(week_day, student_group)
                self.send_message(message='Расписание на завтра:\n' + week_day + '\n' + full_sentence)
            else:
                self.send_message(message='Выходной')
        if response == "на эту неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group) + '\n\n'
            self.send_message(message='Расписание на эту неделю: ' + full_sentence)
        if response == "на следующую неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group, 1) + '\n\n'
            self.send_message(message='Расписание на следующую неделю: ' + full_sentence)
        if response == "какая неделя?":
            self.send_message(message='Сейчас ' + str(self._get_number_week(datetime.now())) + ' неделя.')
        if response == "какая группа?":
            self.send_message(message='Твоя группа ' + users[str(self._user_id)])

    def _make_schedule(self, week_day, student_group, next_week=0):
        schedules_group = student_group[week_day]
        chet_week = (self._get_number_week(datetime.now()) + next_week + 1) % 2
        full_sentence = ""
        for i in range(len(schedules_group)):
            if not schedules_group[i][chet_week]['subject']:
                full_sentence = full_sentence + str(i + 1) + ') --\n'
            else:
                full_sentence = full_sentence + str(i + 1) + ') ' + \
                                schedules_group[i][chet_week]['subject'] + ' ' + \
                                schedules_group[i][chet_week]['lesson_type'] + '.'
                if schedules_group[i][chet_week]['lecturer']:
                    full_sentence = full_sentence + ' Преподаватель: ' + schedules_group[i][chet_week]['lecturer']
                if schedules_group[i][chet_week]['url']:
                    full_sentence = full_sentence + '\nСсылка: ' + schedules_group[i][chet_week]['url']
                full_sentence = full_sentence + '\n'
        return full_sentence

    @staticmethod
    def _get_number_week(day_today: datetime):
        first_week = datetime(2021, 2, 10).isocalendar()[1]
        current_week = day_today.isocalendar()[1]
        number = current_week - first_week + 1
        return number

    def send_meme(self):
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
