import sys
from datetime import datetime, timedelta
from random import randint, choice
from re import findall, sub, IGNORECASE, search
from typing import Tuple, List, Optional, Set

from colorama import Fore, Style
from peewee import DoesNotExist
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from InitConfig import Config
from MySQLStorage import (
    Users_communities, Weeks, Days, Subjects, Lesson_start_end, Users_tasks, Groups, ExamDays, Disciplines
)
from VkBotConstants import ANSI_ESCAPE
from VkBotStatus import States, VkBotStatus


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
    def create_menu(user_message: str, buttons=0, list_of_named_buttons=None) -> VkKeyboard:
        """Создание клавиатуры на основе запроса пользователя.

        Parameters
        ----------
        user_message: str
            сообщение пользователя
        buttons: int
            количество кнопок для добавления
        list_of_named_buttons: list
            список названий для кнопок
        Return
        ----------
        keyboard: VkKeyboard
            клавиатура с командами
        """
        keyboard = VkKeyboard(one_time=True)

        if user_message == 'Продолжить' or user_message == 'Назад':
            keyboard.add_button('Расписание', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('Задачи', color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button('Препод')
            keyboard.add_button('Мем', color=VkKeyboardColor.NEGATIVE)

        if user_message == 'расписание':
            keyboard.add_button('На сегодня', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('На завтра', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('На эту неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_button('На следующую неделю', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Какая неделя?')
            keyboard.add_button('Какая группа?')
            keyboard.add_line()
            keyboard.add_button('Когда обновлялось расписание?', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Назад')

        if user_message == 'препод':
            keyboard.add_button('На эту неделю', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('На следующую неделю', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('Когда обновлялось расписание?', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Назад')

        if user_message == 'мем':
            keyboard.add_button('Случайный мем', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Добавить сообщество', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Удалить сообщество', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('Мои сообщества')
            keyboard.add_line()
            keyboard.add_button('Назад')

        if user_message == 'задачи':
            keyboard.add_button('Добавить задачу', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Удалить задачу', color=VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
            keyboard.add_button('Изменить задачу', color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button('Назад')

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
                        if len(list_of_named_buttons[i]) > 40:
                            print(Fore.LIGHTRED_EX + f"Название кнопки '{list_of_named_buttons[i]}' длиннее 40 символов!" + Style.RESET_ALL)
                        keyboard.add_button(list_of_named_buttons[i][:40])
                    if ((i + 1) % buttons_in_row == 0 and i != 0) or i + 1 == buttons or buttons_in_row == 1:
                        keyboard.add_line()
            keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

        keyboard = keyboard.get_keyboard()
        return keyboard

    def schedule_menu(self, user_message: str, group: Optional[str], state: States) -> str:
        """Обрабатывает запрос пользователя и выдает ответ.

        Parameters
        ----------
        user_message : str
            сообщение пользователя
        group : Optional[str]
            группа пользователя
        state : States
            состояние бота для пользователя
        Return
        ----------
        full_sentence: str
            сообщение для пользователя
        """
        if user_message == "какая группа?":
            return f'Твоя группа {group}.'

        if datetime.now() < Config.get_weeks_info()["start_week"]:
            return "Семестр ещё не начался, расписания нет. Ждём..."

        if Config.get_weeks_info()["pre_exam_week"] < datetime.now():
            return "Семестр закончился, расписание не действительно. Подожди до следующего семестра"

        if user_message in ["на сегодня", "на завтра", "на эту неделю", "на следующую неделю"]:
            lessons_start_end = {
                i.lesson_number: [i.start_time, i.end_time] for i in Lesson_start_end.select().execute()
            }
            start_date = datetime.now() - timedelta(days=datetime.now().isoweekday() - 1)
            if user_message in ["на сегодня", "на завтра"]:
                if user_message == "на сегодня":
                    week_day_number = datetime.now().isoweekday() - 1
                else:
                    week_day_number = datetime.now().isoweekday()
                day_date = start_date + timedelta(days=week_day_number)
                if week_day_number != 6:
                    week_day = self._week_days[week_day_number % 7]
                    full_sentence = self._make_schedule(
                        group,
                        week_day,
                        day_date,
                        lessons_start_end,
                        next_week=datetime.now().isoweekday() - 1 == 6 and user_message == "на завтра"
                    )
                else:
                    week_day = "Воскресенье"
                    full_sentence = ""
                if full_sentence != "":
                    return f'Расписание на {user_message.split(" ")[-1]}:\n\n{week_day} ' \
                           f'({day_date.strftime("%d.%m.%Y")}):\n{full_sentence}'
                else:
                    return f'{user_message.split(" ")[-1].capitalize()} - {week_day} ' \
                           f'({day_date.strftime("%d.%m.%Y")}), выходной.'
            elif user_message in ["на эту неделю", "на следующую неделю"]:
                full_sentence = ""
                if user_message == "на следующую неделю":
                    start_date = start_date + timedelta(days=7)
                if state == States.REQUEST_TEACHER:
                    full_sentence = self.get_teacher_schedule(
                        VkBotStatus.get_data(self._user_id),
                        start_date,
                        lessons_start_end,
                        next_week=user_message == "на следующую неделю"
                    )
                else:
                    for i in range(len(self._week_days)):
                        if i != 0:
                            full_sentence += "▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣\n"
                        week_day_number = i
                        week_day = self._week_days[i]
                        day_date = start_date + timedelta(days=week_day_number)
                        schedule_sentence = self._make_schedule(
                            group,
                            week_day,
                            day_date,
                            lessons_start_end,
                            next_week=user_message == "на следующую неделю"
                        )
                        if schedule_sentence:
                            full_sentence += f'\n{week_day} ({day_date.strftime("%d.%m.%Y")}):\n{schedule_sentence}\n\n'
                        else:
                            full_sentence += f'\n{week_day} ({day_date.strftime("%d.%m.%Y")}) - выходной.\n\n'
                return f'Расписание {user_message}:\n{full_sentence}'
        elif user_message == "какая неделя?":
            week_number = self._get_number_week(datetime.now())
            return f'Сейчас {str(week_number)} неделя. {"Чётная" if week_number % 2 == 0 else "Нечётная"}.'

    @staticmethod
    def get_subjects(teacher: str) -> Tuple[List[Subjects], List[str]]:
        """Получает предметы преподавателя.

        Parameters
        ----------
        teacher : str
            преподаватель
        Return
        ----------
        subjects: List[Subjects]
            список предметов
        teachers: Set[str]
            список преподавателей
        """
        teacher_regex = sub(r"[её]", r"[её]", teacher, flags=IGNORECASE)
        teacher_regex = teacher_regex.rstrip(".")
        subjects = [i for i in Subjects.select().where(
            Subjects.teacher.iregexp(teacher_regex)
        ).execute()]
        teachers = set(t.teacher for t in subjects)
        if any("\n" in t for t in teachers):
            teachers = list(teachers)
            for i in range(len(teachers)):
                if "\n" in teachers[i]:
                    new_str = "-"
                    for part in teachers[i].split("\n"):
                        if search(teacher_regex, part, flags=IGNORECASE):
                            new_str = part.strip(" .")
                            break
                    teachers[i] = new_str
            teachers = set(teachers)

        return subjects, list(teachers)

    def get_teacher_schedule(self, teacher: str, day_date: datetime, lessons_start_end: dict, next_week=False):
        """Преобразует расписание преподавателя в сообщение для пользователя.

        Parameters
        ----------
        teacher : str
            преподаватель
        day_date: datetime
            День недели в формате datetime
        lessons_start_end : dict
            словарь начала и окончания каждой пары
        next_week : bool
            вывод на следующую неделю (по умолчанию на эту)
        Return
        ----------
        full_sentence: str
            преобразованная строка
        """
        full_sentence = ""
        space = "&#8194;"
        thin_space = "&#8201;"
        new_line = '\n'
        even_week = bool((self._get_number_week(datetime.now()) + int(next_week) + 1) % 2)

        try:
            subjects, _ = self.get_subjects(teacher)
            if len(subjects) == 0:
                raise DoesNotExist()

            subj_ids = set(i.schedule_of_subject_id for i in subjects)

            schedules_of_day: List[Days] = [i for i in Days.select().where(
                Days.subject_schedules_of_day_id.in_(subj_ids)).execute()]

            sch_ids = set(i.day_of_week_id for i in schedules_of_day)

            weeks: List[Weeks] = [i for i in Weeks.select().where(
                (Weeks.days_of_group_id.in_(sch_ids)) & (Weeks.even == even_week)).execute()]

            group_ids = set(i.group_id for i in weeks)

            groups_dict = {}
            for g in Groups.select().where(Groups.group_id.in_(group_ids)).execute():
                groups_dict[g.group_id] = g.group

            weeks_ids = set(i.days_of_group_id for i in weeks)

            schedules_of_day = sorted(
                list(filter(
                    lambda s: s.day_of_week_id in weeks_ids,
                    schedules_of_day
                )),
                key=lambda s: s.subject_schedules_of_day_id
            )

            schedules_of_days = []
            for d in self._week_days:
                schedules_of_days += [[]]
                for s in schedules_of_day:
                    if s.day_of_week == d:
                        schedules_of_days[-1] += [s]
                if len(schedules_of_days[-1]) == 0:
                    schedules_of_days.pop()

            for i in range(len(schedules_of_days)):
                if i != 0:
                    full_sentence += "\n\n▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣\n"
                week_day = schedules_of_days[i][0].day_of_week
                full_sentence += f'\n{week_day} (' + (
                        day_date + timedelta(days=self._week_days.index(week_day))
                ).strftime("%d.%m.%Y") + '):\n'
                subj_ids_from_days = [d.subject_schedules_of_day_id for d in schedules_of_days[i]]

                def ch(s: Subjects):
                    cur_day = None
                    for d in schedules_of_days[i]:
                        if d.subject_schedules_of_day_id == s.schedule_of_subject_id:
                            cur_day = d
                            break
                    if cur_day is None:
                        return s, None
                    group = [groups_dict[w.group_id] for w in weeks if w.days_of_group_id == cur_day.day_of_week_id]
                    return s, group

                subj_day = []
                for subj in map(ch, filter(lambda s: s.schedule_of_subject_id in subj_ids_from_days, subjects)):
                    for s in range(len(subj_day)):
                        if subj_day[s][0].lesson_number == subj[0].lesson_number and \
                                subj_day[s][0].subject.lower() == subj[0].subject.lower() and \
                                subj_day[s][0].teacher.lower() == subj[0].teacher.lower():
                            subj_day[s][1].extend(subj[1])
                            break
                    else:
                        subj_day.append(subj)
                subj_day = sorted(subj_day, key=lambda s: s[0].lesson_number)

                for subj in range(len(subj_day)):
                    if subj != 0:
                        full_sentence += f"{space * 2}------------------------------\n"
                    full_sentence += space * 2
                    full_sentence += f"{subj_day[subj][0].lesson_number} пара: с "
                    full_sentence += f"{lessons_start_end[subj_day[subj][0].lesson_number][0].strftime('%H:%M')} " \
                                     f"по {lessons_start_end[subj_day[subj][0].lesson_number][1].strftime('%H:%M')}" \
                                     f"\n{space * 4}{subj_day[subj][0].subject.replace(new_line, f'{new_line}{space * 4}')}"
                    if subj_day[subj][0].lesson_type:
                        type_subj_l = subj_day[subj][0].lesson_type.split(new_line)
                        if all(all(i == type_subj_l[j] for i in type_subj_l) for j in range(len(type_subj_l))):
                            full_sentence += f"\n{space * 4}Вид занятия: {type_subj_l[0]}"
                        else:
                            full_sentence += f"\n{space * 4}Виды занятий: {', '.join(type_subj_l)}"
                    if subj_day[subj][0].teacher:
                        if len(subj_day[subj][0].teacher.split(new_line)) == 1:
                            full_sentence += f"\n{space * 4}Препод: {subj_day[subj][0].teacher} "
                        else:
                            full_sentence += f"\n{space * 4}Преподы: {subj_day[subj][0].teacher.replace(new_line, f'{new_line}{space * 13} ')}"
                    if subj_day[subj][0].class_number:
                        audit_subj_l = subj_day[subj][0].class_number.split(new_line)
                        if len(audit_subj_l) == 1 or \
                                all(all(i == audit_subj_l[j] for i in audit_subj_l) for j in range(len(audit_subj_l))):
                            full_sentence += f"\n{space * 4}Аудитория: {audit_subj_l[0]}"
                        else:
                            full_sentence += f"\n{space * 4}Аудитории: {subj_day[subj][0].class_number.replace(new_line, f'{new_line}{space * 14} {thin_space}')}"
                    if subj_day[subj][1] is not None:
                        if len(subj_day[subj][1]) == 1:
                            full_sentence += f"\n{space * 4}Группа: {subj_day[subj][1][0]}"
                        else:
                            full_sentence += f"\n{space * 4}Группы: {f', '.join(subj_day[subj][1])}"
                    full_sentence += "\n"
        except DoesNotExist:
            full_sentence += "\nДанные по расписанию не доступны\nПопробуйте изменить имя препода"
        return full_sentence

    def _make_schedule(self, group: str, week_day: str,
                       day_date: datetime, lessons_start_end: dict, next_week=False) -> str:
        """Преобразует часть расписания в сообщение для пользователя.

        Parameters
        ----------
        group : str
            группа пользователя
        week_day : str
            день недели
        day_date: datetime
            День недели в формате datetime
        lessons_start_end : dict
            словарь начала и окончания каждой пары
        next_week : bool
            вывод на следующую неделю (по умолчанию на эту)
        Return
        ----------
        full_sentence: str
            преобразованная строка
        """
        full_sentence = ""
        space = "&#8194;"
        thin_space = "&#8201;"
        new_line = '\n'
        even_week = bool((self._get_number_week(datetime.now()) + int(next_week) + 1) % 2)
        dates_of_tasks = self.get_user_tasks_on_day(day_date)

        if len(list(Groups.select().where(Groups.group == group).limit(1).execute())) == 0:
            return f"Для этой группы \"{group}\" нет расписания!"

        group_id = Groups.get(Groups.group == group).group_id
        if len(list(Weeks.select().where((Weeks.group_id == group_id) &
                                         (Weeks.even == even_week)).limit(1).execute())) == 0 and \
                len(list(ExamDays.select().where((ExamDays.group_id == group_id) &
                                                 (ExamDays.day_date == day_date.date())).limit(1).execute())) == 0:
            return ""

        # Usual schedule
        try:
            day_of_group_id = Weeks.get((Weeks.group_id == group_id) & (Weeks.even == even_week)).days_of_group_id

            schedules_of_day = Days.get(
                (Days.day_of_week_id == day_of_group_id) & (Days.day_of_week == week_day)).subject_schedules_of_day_id

            subjects = [i for i in
                        Subjects.select().where(Subjects.schedule_of_subject_id == schedules_of_day).execute()]
        except DoesNotExist:
            subjects = []

        week_number = VkBotFunctions._get_number_week(day_date)
        full_list = []
        task_list = [[i.start_date.time(), i.end_date.time(), i.task] for i in dates_of_tasks]
        for i in subjects:
            if i.subject:
                lesson_start_time = lessons_start_end[i.lesson_number][0]
                lesson_end_time = lessons_start_end[i.lesson_number][1]
                is_place_empty = True
                for j in task_list:
                    if (j[0] < lesson_start_time < j[1]) or (j[0] < lesson_end_time < j[1]) or \
                            (j[0] > lesson_start_time < j[1] < lesson_end_time > j[0]) or \
                            (j[0] == lesson_start_time and j[1] == lesson_end_time):
                        is_place_empty = False
                        break
                if "н." in i.subject.lower() and "кр." not in i.subject.lower() and is_place_empty:
                    search_range = [str_i.split("н.")[0] for str_i in i.subject.split("\n")
                                    if findall(r"\d+", str_i.split("н.")[0])]
                    is_place_empty_list = []
                    for search_string in search_range:
                        is_place_empty = True
                        matches = findall(r"\d+-\d+", search_string)
                        if len(matches) > 0:
                            for f in matches:
                                if int(f.split("-")[0]) > week_number or week_number > int(f.split("-")[1]):
                                    is_place_empty = False
                                    break
                            is_place_empty_list.append(is_place_empty)
                        matches = findall(r"\d+", search_string)
                        if len(matches) > 0:
                            if not any([int(q) == week_number for q in matches]):
                                is_place_empty_list.append(False)
                            else:
                                is_place_empty_list.append(True)
                    is_place_empty = any(is_place_empty_list) if len(is_place_empty_list) != 0 else True
                if is_place_empty:
                    full_list.append([lesson_start_time, lesson_end_time, i.subject, i.lesson_number,
                                      i.lesson_type, i.teacher, i.class_number, i.link])

        # Exam schedule
        try:
            discipline_id = ExamDays.get((ExamDays.group_id == group_id) &
                                         (ExamDays.day_date == day_date.date())).discipline_id

            disciplines: List[Disciplines] = [i for i in Disciplines.select().where(Disciplines.discipline_id == discipline_id).execute()]
        except DoesNotExist:
            disciplines = []

        for i in disciplines:
            if i.discipline:
                lesson_start_time = i.discipline_time
                lesson_end_time = i.discipline_time_end
                is_place_empty = True
                if lesson_end_time is None:
                    for j in task_list:
                        if j[0] < lesson_start_time < j[1] or j[0] > lesson_start_time < j[1] or \
                                j[0] == lesson_start_time:
                            is_place_empty = False
                            break
                else:
                    for j in task_list:
                        if (j[0] < lesson_start_time < j[1]) or (j[0] < lesson_end_time < j[1]) or \
                                (j[0] > lesson_start_time < j[1] < lesson_end_time > j[0]) or \
                                (j[0] == lesson_start_time and j[1] == lesson_end_time):
                            is_place_empty = False
                            break
                if is_place_empty:
                    full_list.append([lesson_start_time, lesson_end_time, i.discipline, None,
                                      i.discipline_type, i.examiner, i.class_number, i.link])

        full_list.extend(task_list)
        full_list.sort(key=lambda x: x[0])

        for sbj_tsk in range(len(full_list)):
            if sbj_tsk != 0:
                full_sentence += f"{space * 2}------------------------------\n"
            full_sentence += space * 2
            if len(full_list[sbj_tsk]) > 3 and full_list[sbj_tsk][3] is not None:
                full_sentence += f"{full_list[sbj_tsk][3]} пара: с "
            else:
                full_sentence += "С "
            full_sentence += f"{full_list[sbj_tsk][0].strftime('%H:%M')}"
            if full_list[sbj_tsk][1] is not None:
                full_sentence += f" по {full_list[sbj_tsk][1].strftime('%H:%M')}"
            full_sentence += f"\n{space * 4}{full_list[sbj_tsk][2].replace(new_line, f'{new_line}{space * 4}')}"
            if len(full_list[sbj_tsk]) > 3:
                if full_list[sbj_tsk][4]:
                    type_subj_l = full_list[sbj_tsk][4].split(new_line)
                    if all(all(i == type_subj_l[j] for i in type_subj_l) for j in range(len(type_subj_l))):
                        full_sentence += f"\n{space * 4}Вид занятия: {type_subj_l[0]}"
                    else:
                        full_sentence += f"\n{space * 4}Виды занятий: {', '.join(type_subj_l)}"
                if full_list[sbj_tsk][5]:
                    if len(full_list[sbj_tsk][5].split(new_line)) == 1:
                        full_sentence += f"\n{space * 4}Препод: {full_list[sbj_tsk][5]} "
                    else:
                        full_sentence += f"\n{space * 4}Преподы: {full_list[sbj_tsk][5].replace(new_line, f'{new_line}{space * 13} ')}"
                if full_list[sbj_tsk][6]:
                    audit_subj_l = full_list[sbj_tsk][6].split(new_line)
                    if len(audit_subj_l) == 1 or \
                            all(all(i == audit_subj_l[j] for i in audit_subj_l) for j in range(len(audit_subj_l))):
                        full_sentence += f"\n{space * 4}Аудитория: {audit_subj_l[0]}"
                    else:
                        full_sentence += f"\n{space * 4}Аудитории: {full_list[sbj_tsk][6].replace(new_line, f'{new_line}{space * 14} {thin_space}')}"
                if full_list[sbj_tsk][7]:
                    if len(full_list[sbj_tsk][7].split(new_line)) == 1:
                        full_sentence += f"\n{space * 4}Ссылка: {full_list[sbj_tsk][7]}"
                    else:
                        full_sentence += f"\n{space * 4}Ссылки: {full_list[sbj_tsk][7].replace(new_line, f'{new_line}{space * 12} ')}."
            full_sentence += "\n"
        return full_sentence

    @staticmethod
    def _get_number_week(day_today: datetime) -> int:
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
        first_week = Config.get_weeks_info()["start_week"].isocalendar()[1]
        current_week = day_today.isocalendar()[1]
        number = current_week - first_week + 1
        return number

    def get_user_tasks_on_day(self, date_of_day: datetime) -> List[Users_tasks]:
        """Получение задач пользователя на данный день.

        Parameters
        ----------
        date_of_day: datetime
            нужная дата
        Return
        ----------
        users_tasks: List[Users_tasks]
            лист из задач пользователя
        """
        min_date = datetime.combine(date_of_day.date(), datetime.min.time())
        max_date = datetime.combine(date_of_day.date(), datetime.max.time())

        return [i for i in Users_tasks.select().where((Users_tasks.user_id == self._user_id) &
                                                      (Users_tasks.start_date >= min_date) &
                                                      (Users_tasks.start_date <= max_date)).execute()]

    def send_meme(self, vk_session_user) -> Tuple[str, str]:
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
        max_photo_width = 0
        photo_url = None
        for i in photo_sizes:
            if i['height'] > max_photo_height:
                max_photo_height = i['height']
            if i['width'] > max_photo_width:
                max_photo_width = i['width']
        for i in photo_sizes:
            if i['height'] == max_photo_height and i['width'] == max_photo_width:
                photo_url = i['url']
                break
        if photo_url is None:
            for i in photo_sizes:
                if i['height'] == max_photo_height:
                    photo_url = i['url']
                    break

        return photo_url, choice(self._300_answers)

    def change_users_community(self, vk_session_user, need_delete: bool, communities_names: list) -> bool:
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

    def show_users_communities(self, vk_session_user, show_name=False, show_url=False) -> Tuple[bool, list]:
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


class OutputFileHandler:
    def __init__(self, file=None):
        self.file = file
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        if self.file is not None:
            self.file.close()

    def write(self, data, **kwargs):
        if data != "\n":
            if self.file is not None:
                self.file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                                f"{ANSI_ESCAPE.sub('', data)}")
            self.stdout.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {data}")
        else:
            if self.file is not None:
                self.file.write(data)
            self.stdout.write(data)
        self.flush()
        if kwargs.pop('flush', False):
            self.stdout.flush()

    def flush(self):
        if self.file is not None:
            self.file.flush()
