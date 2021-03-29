from datetime import datetime

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class VkBotFunctions:
    """Основные функции бота.

    Parameters
    ----------
    user_id : int
        id пользователя
    """

    def __init__(self, user_id):
        self._week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        self._user_id = user_id

    @staticmethod
    def create_menu(user_message):
        """Создание клавиатуры на основе запроса пользователя.

        :param user_message: сообщение пользователя
        :type user_message: str
        :rtype: VkKeyboard
        :return: клавиатура с командами
        """
        keyboard = VkKeyboard(one_time=True)

        if user_message == 'Продолжить':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Случайный мем')
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

        keyboard = keyboard.get_keyboard()
        return keyboard

    def schedule_menu(self, user_message, schedules, users):
        """Обрабатывает запрос пользователя и выдает ответ.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        schedules : dict
            расписание
        users : dict
            кэш пользователей
        Return
        ----------
        full_sentence: str
            сообщение для пользователя
        """
        if user_message == "на сегодня":
            week_day = datetime.now().isoweekday() - 1
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence = self._make_schedule(week_day, student_group)
                return 'Расписание на сегодня:\n' + week_day + '\n' + full_sentence
            else:
                return 'Выходной'
        if user_message == "на завтра":
            week_day = datetime.now().isoweekday()
            if week_day == 7:
                week_day = 0
            if week_day < 6:
                week_day = self._week_days[week_day]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence = self._make_schedule(week_day, student_group)
                return 'Расписание на завтра:\n' + week_day + '\n' + full_sentence
            else:
                return 'Выходной'
        if user_message == "на эту неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group) + '\n\n'
            return 'Расписание на эту неделю: ' + full_sentence
        if user_message == "на следующую неделю":
            full_sentence = ""
            for i in range(len(self._week_days)):
                week_day = self._week_days[i]
                student_group = schedules["groups"][users[str(self._user_id)]]
                full_sentence += '\n' + week_day + ':\n' + self._make_schedule(week_day, student_group, 1) + '\n\n'
            return 'Расписание на следующую неделю: ' + full_sentence
        if user_message == "какая неделя?":
            return 'Сейчас ' + str(self._get_number_week(datetime.now())) + ' неделя.'
        if user_message == "какая группа?":
            return 'Твоя группа ' + users[str(self._user_id)]

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
        """Получение номера недели."""
        first_week = datetime(2021, 2, 10).isocalendar()[1]
        current_week = day_today.isocalendar()[1]
        number = current_week - first_week + 1
        return number

