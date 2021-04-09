from datetime import datetime
from random import randint, choice

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from MySQLStorage import Users_communities


class VkBotFunctions:
    """Основные функции бота.

    Parameters
    ----------
    user_id : int
        id пользователя
    """

    _300_communities = [
        45045130,  # - МЕМЫ
        45523862,  # - Томат
        67580761,  # - КБ
        57846937,  # - MDK
        12382740,  # - ЁП
        45745333,  # - 4ch
        76628628,  # - Silvername
    ]

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

    def __init__(self, user_id):
        self._week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        self._user_id = user_id

    @staticmethod
    def create_menu(user_message, buttons = 0):
        """Создание клавиатуры на основе запроса пользователя.

        Parameters
        ----------
        user_message: str
            сообщение пользователя
        buttons: int
            количество кнопок для добавления
        Return
        ----------
        keyboard: VkKeyboard
            клавиатура с командами

        """
        keyboard = VkKeyboard(one_time=True)

        if user_message == 'Продолжить':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Мем')
            keyboard.add_line()
            keyboard.add_button('Добавить задачу', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Изменить задачу', color=VkKeyboardColor.NEGATIVE)

        if user_message == 'расписание':
            keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Какая неделя?')
            keyboard.add_button('Какая группа?')

        if user_message == 'мем':
            keyboard.add_button('Случайный мем', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Добавить сообщество', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Удалить сообщество', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('Мои сообщества')

        if user_message == 'клавиатура--отмена':
            if buttons != 0:
                buttons_in_row = None
                stages = [0, 3, 9, 16, 21, 26]
                for i in range(len(stages)):
                    if buttons < stages[i]:
                        buttons_in_row = i
                        break
                    elif buttons >= stages[-1]:
                        buttons_in_row = len(stages) - 1
                        break
                buttons = buttons if buttons < stages[-1] else stages[-1] - 1
                for i in range(buttons):
                    keyboard.add_button(str(i + 1))
                    if ((i + 1) % buttons_in_row == 0 and i != 0) or i + 1 == buttons or buttons_in_row == 1:
                        keyboard.add_line()
            keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

        keyboard = keyboard.get_keyboard()
        return keyboard

    def schedule_menu(self, user_message, schedules, group):
        """Обрабатывает запрос пользователя и выдает ответ.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        schedules : dict
            расписание
        group : str
            группа пользователя
        Return
        ----------
        full_sentence: str
            сообщение для пользователя
        """
        if user_message == "на сегодня":
            week_day = datetime.now().isoweekday() - 1
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][group]
                full_sentence = self._make_schedule(week_day, student_group)
                return 'Расписание на сегодня:\n' + week_day + '\n' + full_sentence
            else:
                return 'Выходной'
        elif user_message == "на завтра":
            week_day = datetime.now().isoweekday()
            if week_day == 7:
                week_day = 0
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][group]
                full_sentence = self._make_schedule(week_day, student_group)
                return 'Расписание на завтра:\n' + week_day + '\n' + full_sentence
            else:
                return 'Выходной'
        elif user_message == "на эту неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][group]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group) + '\n\n'
            return 'Расписание на эту неделю: ' + full_sentence
        elif user_message == "на следующую неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][group]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group, 1) + '\n\n'
            return 'Расписание на следующую неделю: ' + full_sentence
        elif user_message == "какая неделя?":
            return 'Сейчас ' + str(self._get_number_week(datetime.now())) + ' неделя.'
        elif user_message == "какая группа?":
            return 'Твоя группа ' + group
        else:
            return "Я не знаю такой команды"

    def _make_schedule(self, week_day, student_group, next_week=0):
        """Преобразует часть расписание в сообщение для пользователя.

        Parameters
        ----------
        week_day : str
            день недели
        student_group : str
            группа пользователя
        next_week : int
            вывод на следующую неделю (по умолчанию на эту)
        Return
        ----------
        full_sentence: str
            преобразованная строка
        """
        schedules_group = student_group[week_day]
        chet_week = (self._get_number_week(datetime.now()) + next_week + 1) % 2
        full_sentence = ""
        for i in range(len(schedules_group)):
            if not schedules_group[i][chet_week]['subject']:
                full_sentence = full_sentence + str(schedules_group[i][chet_week]['lesson_number']) + ') --\n'
            else:
                full_sentence = full_sentence + str(schedules_group[i][chet_week]['lesson_number']) + ') ' + \
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
        """Получение номера недели.

        Parameters
        ----------
        day_today: datetime
            сегодняшняя дата
        Return
        ----------
        number: int
            номер недели
        """
        first_week = datetime(2021, 2, 10).isocalendar()[1]
        current_week = day_today.isocalendar()[1]
        number = current_week - first_week + 1
        return number

    def send_meme(self, vk_session_user):
        """Отправляет пользователю случайный мем.

        Parameters
        ----------
        vk_session_user: VkApi
            пользователь для работы с мемами
        Return
        ----------
        photo_url: str
            ссылка на картинку
        choice: str
            случайное сообщение из списка к картинке
        """
        if len([i for i in Users_communities.select()
                .where(Users_communities.user_id == self._user_id).limit(1).execute()]) != 0:
            communities = [i for i in
                           Users_communities.select().where(Users_communities.user_id == self._user_id).execute()]
            communities = [i.community_id for i in communities]
            own_id = choice(communities)
        else:
            own_id = choice(self._300_communities)
        # Тырим с вк фотки)
        vk = vk_session_user.get_api()
        photos_count = vk.photos.get(owner_id=-own_id, album_id="wall", count=1).get('count')
        photo_sizes = vk.photos.get(owner_id=-own_id,
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

        return photo_url, choice(self._300_answers)

    def change_users_community(self, vk_session_user, need_delete: bool, communities_names):
        """Добавляет или удаляет сообщества из таблицы

        Parameters
        ----------
        vk_session_user: VkApi
            пользователь для работы с мемами
        need_delete: bool
            удалить или сохранить
        communities_names: list
            названия групп
        Return
        ----------
        need_delete: bool
            удалено или добавлено было сообщество
        """
        vk = vk_session_user.get_api()
        communities = vk.groups.getById(group_ids=communities_names)  # get ids of groups
        communities_ids = [int(i['id']) for i in communities]
        for community_id in communities_ids:
            if len([i for i in Users_communities.select()
                    .where(Users_communities.user_id == self._user_id and
                           Users_communities.community_id == community_id).limit(1).execute()]) != 0:
                if need_delete:
                    Users_communities.delete().where(Users_communities.user_id == self._user_id and
                                                     Users_communities.community_id == community_id).execute()
            else:
                if not need_delete:
                    Users_communities.create(user_id=self._user_id, community_id=community_id)
        return need_delete

    def show_users_communities(self, vk_session_user, show_name=False, show_url=False):
        """Возвращает список сообществ из таблицы и стандартные это сообщества или собственные пользователя

        Parameters
        ----------
        vk_session_user: VkApi
            пользователь для работы с мемами
        show_name: bool
            нужно ли показывать имена
        show_url: bool
            нужно ли показывать ссылки
        Return
        ----------
        communities_from: bool
            сообщества от пользователя или из стандартных бота
        communities_list: list
            список сообществ
        """
        communities = []
        if len([i for i in Users_communities.select()
                .where(Users_communities.user_id == self._user_id).limit(1).execute()]) != 0:
            communities = [i for i in
                           Users_communities.select().where(Users_communities.user_id == self._user_id).execute()]
            communities = [i.community_id for i in communities]
        vk = vk_session_user.get_api()
        communities_list = []
        if len(communities) > 0:
            communities_list = vk.groups.getById(group_ids=communities)
        else:
            if not show_url:
                communities_list = vk.groups.getById(group_ids=self._300_communities)
        if show_name and show_url and len(communities) > 0:
            communities_list = [i['name'] + " (https://vk.com/" + i['screen_name'] + ")" for i in communities_list]
        elif show_name:
            communities_list = [i['name'] for i in communities_list]
        elif show_url and len(communities) > 0:
            communities_list = ["https://vk.com/" + i['screen_name'] for i in communities_list]
        return len(communities) > 0, communities_list
