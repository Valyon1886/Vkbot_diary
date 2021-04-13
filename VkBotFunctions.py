from datetime import datetime
from random import randint, choice

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from peewee import DoesNotExist

from MySQLStorage import Users_communities, Weeks, Days, Subjects, Lesson_start_end


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
    def create_menu(user_message: str, buttons=0, list_of_named_buttons=None):
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
        list_of_named_buttons : list
            список названий кнопок
        """
        keyboard = VkKeyboard(one_time=True)

        if user_message == 'Продолжить':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Задачи', color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button('Мем')

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

        if user_message == 'задачи':
            keyboard.add_button('Добавить задачу', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Удалить задачу', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('Изменить задачу', color=VkKeyboardColor.PRIMARY)

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
                if list_of_named_buttons is not None:
                    list_of_named_buttons = list_of_named_buttons \
                        if len(list_of_named_buttons) < stages[-1] \
                        else list_of_named_buttons[:stages[-1] - 1]
                for i in range(buttons):
                    if list_of_named_buttons is None:
                        keyboard.add_button(str(i + 1))
                    else:
                        keyboard.add_button(list_of_named_buttons[i])
                    if ((i + 1) % buttons_in_row == 0 and i != 0) or i + 1 == buttons or buttons_in_row == 1:
                        keyboard.add_line()
            keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

        keyboard = keyboard.get_keyboard()
        return keyboard

    def schedule_menu(self, user_message: str, group: str):
        """Обрабатывает запрос пользователя и выдает ответ.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        group : str
            группа пользователя
        Return
        ----------
        full_sentence: str
            сообщение для пользователя
        """
        if user_message in ["на сегодня", "на завтра", "на эту неделю", "на следующую неделю"]:
            lessons_start_end = {i.lesson_number: [i.start_time, i.end_time]
                                 for i in Lesson_start_end.select().execute()}
            if user_message in ["на сегодня", "на завтра"]:
                if user_message == "на сегодня":
                    week_day = datetime.now().isoweekday() - 1
                else:
                    week_day = datetime.now().isoweekday()
                    if week_day == 7:
                        week_day = 0
                if week_day < 6:
                    week_day = self._week_days[week_day]
                    full_sentence = self._make_schedule(group, week_day, lessons_start_end, one_day=True)
                else:
                    week_day = "Воскресенье"
                    full_sentence = ""
                if full_sentence != "":
                    return f'Расписание на {user_message.split(" ")[-1]}:\n{week_day}\n{full_sentence}'
                else:
                    return f'{user_message.split(" ")[-1].capitalize()} - {week_day.lower()}, выходной.'
            elif user_message in ["на эту неделю", "на следующую неделю"]:
                full_sentence = ""
                for i in range(len(self._week_days)):
                    week_day = self._week_days[i]
                    full_sentence += f'\n{week_day}:\n' + \
                                     self._make_schedule(group,
                                                         week_day,
                                                         lessons_start_end,
                                                         next_week=user_message == "на следующую неделю") + '\n\n'
                return f'Расписание {user_message}: {full_sentence}'
        elif user_message == "какая неделя?":
            return f'Сейчас {str(self._get_number_week(datetime.now()))} неделя.'
        elif user_message == "какая группа?":
            return f'Твоя группа {group}.'
        else:
            return "Я не знаю такой команды."

    def _make_schedule(self, group: str, week_day: str, lessons_start_end: dict, one_day=False, next_week=False):
        """Преобразует часть расписание в сообщение для пользователя.

        Parameters
        ----------
        group : str
            группа пользователя
        week_day : str
            день недели
        lessons_start_end : dict
            словарь начала и окончания каждой пары
        one_day : bool
            вывод на один день или несколько (по умолчанию на несколько)
        next_week : bool
            вывод на следующую неделю (по умолчанию на эту)
        Return
        ----------
        full_sentence: str
            преобразованная строка
        """
        even_week = bool((self._get_number_week(datetime.now()) + int(next_week) + 1) % 2)
        try:
            day_of_group_id = Weeks.get((Weeks.group == group) & (Weeks.even == even_week)).days_of_group_id

            schedules_of_day = Days.get(
                (Days.day_of_week_id == day_of_group_id) & (Days.day_of_week == week_day)).subject_schedules_of_day_id

            subjects = [i for i in
                        Subjects.select().where(Subjects.schedule_of_subject_id == schedules_of_day).execute()]
            if len(subjects) == 0:
                raise DoesNotExist
        except DoesNotExist:
            return "Данные не доступны"

        full_sentence = ""
        any_subject = any([bool(i.subject) for i in subjects])
        for subj in subjects:
            if not subj.subject:
                if not one_day or any_subject:
                    full_sentence += f"{str(subj.lesson_number)}) " \
                                     f"c {lessons_start_end[subj.lesson_number][0].strftime('%H:%M')} " \
                                     f"по {lessons_start_end[subj.lesson_number][1].strftime('%H:%M')}\n --\n"
            else:
                full_sentence += f"{str(subj.lesson_number)}) " \
                                 f"c {lessons_start_end[subj.lesson_number][0].strftime('%H:%M')} " \
                                 f"по {lessons_start_end[subj.lesson_number][1].strftime('%H:%M')}\n" \
                                 f"{subj.subject} {subj.lesson_type}. "
                if subj.teacher:
                    full_sentence += f"Преподаватель: {subj.teacher} "
                if subj.class_number:
                    full_sentence += f"Аудитория: {subj.class_number}"
                if subj.link:
                    full_sentence += f"\nСсылка: {subj.link}"
                full_sentence += "\n"
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
            communities = [i.community_id for i in
                           Users_communities.select().where(Users_communities.user_id == self._user_id).execute()]
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

    def change_users_community(self, vk_session_user, need_delete: bool, communities_names: list):
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
                    .where((Users_communities.user_id == self._user_id) &
                           (Users_communities.community_id == community_id)).limit(1).execute()]) != 0:
                if need_delete:
                    Users_communities.delete().where((Users_communities.user_id == self._user_id) &
                                                     (Users_communities.community_id == community_id)).execute()
            else:
                if not need_delete:
                    Users_communities.create(user_id=self._user_id, community_id=community_id)
        return need_delete

    def show_users_communities(self, vk_session_user, show_name=False, show_url=False):
        """Возвращает список сообществ из таблицы и стандартные ли это сообщества или собственные пользователя

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
            communities = [i.community_id for i in
                           Users_communities.select().where(Users_communities.user_id == self._user_id).execute()]
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
