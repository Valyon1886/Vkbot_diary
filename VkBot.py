import datetime

from vk_api import VkUpload
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class VkBot:
    def __init__(self, ):
        self.week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

    def send_message(self, vk_session, id, rand_id, message=None, keyboard=None):
        vk_session.method('messages.send',
                          {'user_id': id, 'message': message, 'random_id': rand_id, 'keyboard': keyboard})

    def send_pic(self, vk_session, id, response):
        response.save('img.png')
        upload = VkUpload(vk_session)
        photo = upload.photo_messages('img.png')
        image = "photo{}_{}".format(photo[0]["owner_id"], photo[0]["id"])
        vk_session.method('messages.send', {'user_id': id, 'random_id': get_random_id(), "attachment": image})

    def menu(self, response):
        keyboard = VkKeyboard(one_time=True)

        if response == 'Продолжить':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)

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

    def schedule_menu(self, response, vk_session, id, rand_id, schedules, users):
        if response == "на сегодня":
            week_day = datetime.datetime.now().isoweekday() - 1
            if week_day < 6:
                week_day = self.week_days[week_day]
                student_group = schedules["groups"][users[str(id)]]
                full_sentence = self.make_schedule(week_day, student_group)
                self.send_message(vk_session, id, rand_id,
                             message='Расписание на сегодня:\n' + week_day + '\n' + full_sentence)
            else:
                self.send_message(vk_session, id, rand_id, message='Выходной')
        if response == "на завтра":
            week_day = datetime.datetime.now().isoweekday()
            if week_day == 7:
                week_day = 0
            if week_day < 6:
                week_day = self.week_days[week_day]
                student_group = schedules["groups"][users[str(id)]]
                full_sentence = self.make_schedule(week_day, student_group)
                self.send_message(vk_session, id, rand_id,
                             message='Расписание на завтра:\n' + week_day + '\n' + full_sentence)
            else:
                self.send_message(vk_session, id, rand_id, message='Выходной')
        if response == "на эту неделю":
            full_sentence = ""
            for i in range(len(self.week_days)):
                week_day = self.week_days[i]
                student_group = schedules["groups"][users[str(id)]]
                full_sentence += '\n' + week_day + ':\n' + self.make_schedule(week_day, student_group) + '\n\n'
            self.send_message(vk_session, id, rand_id, message='Расписание на эту неделю: ' + full_sentence)
        if response == "на следующую неделю":
            full_sentence = ""
            for i in range(len(self.week_days)):
                week_day = self.week_days[i]
                student_group = schedules["groups"][users[str(id)]]
                full_sentence += '\n' + week_day + ':\n' + self.make_schedule(week_day, student_group, 1) + '\n\n'
            self.send_message(vk_session, id, rand_id, message='Расписание на следующую неделю: ' + full_sentence)
        if response == "какая неделя?":
            self.send_message(vk_session, id, rand_id,
                         message='Сейчас ' + str(self.number_week(datetime.datetime.now())) + ' неделя.')
        if response == "какая группа?":
            self.send_message(vk_session, id, rand_id, message='Твоя группа ' + users[str(id)])

    def number_week(self, day_today):
        first_week = datetime.datetime(2021, 2, 10).isocalendar()[1]
        current_week = day_today.isocalendar()[1]
        number = current_week - first_week
        return number

    def make_schedule(self, week_day, student_group, next_week=0):
        schedules_group = student_group[week_day]
        chet_week = (self.number_week(datetime.datetime.now()) + next_week) % 2
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