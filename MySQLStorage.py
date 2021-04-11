from peewee import *

from InitSQL import InitSQL


class BaseModel(Model):
    """Базовая модель таблицы для базы данных"""

    class Meta:
        database = InitSQL.get_DB()


class Subjects(BaseModel):
    """Таблица информации о каждой паре"""
    schedule_of_subject_id = IntegerField(column_name='ScheduleOfSubjectId')
    lesson_number = IntegerField(column_name='LessonNumber')
    subject = TextField(column_name='Subject')
    lesson_type = TextField(column_name='LessonType')
    teacher = TextField(column_name='Teacher')
    class_number = TextField(column_name='ClassNumber')
    link = TextField(column_name='Link')

    class Meta:
        table_name = 'Subjects'


class Days(BaseModel):
    """Таблица id пар для дней"""
    day_of_week_id = IntegerField(column_name='DayOfWeekId')
    day_of_week = TextField(column_name='DayOfWeek')
    # schedule_of_subject = ForeignKeyField(Subjects, to_field='schedule_id')
    subject_schedules_of_day_id = IntegerField(column_name='SubjectScheduleOfDayId')

    class Meta:
        table_name = 'Days'


class Weeks(BaseModel):
    """Таблица id дней для выбранной группы и нечётной/чётной недели"""
    week_id = AutoField(column_name='WeekId')
    group = TextField(column_name='Group')
    even = BooleanField(column_name='Even')
    # day_lesson = ForeignKeyField(Days, to_field='day_lesson_id')
    days_of_group_id = IntegerField(column_name='DaysOfGroupId')

    class Meta:
        table_name = 'Weeks'


class Users_groups(BaseModel):
    """Таблица выбранных групп для каждого пользователя"""
    user_id = IntegerField(column_name='UserId')
    group = TextField(column_name='Group')

    class Meta:
        table_name = 'Users_groups'


class Users_notes(BaseModel):
    """Таблица заметок для каждого пользователя на выбранные даты"""
    user_id = IntegerField(column_name='UserId')
    start_date = DateTimeField(column_name='StartDate')
    end_date = DateTimeField(column_name='EndDate')
    note = TextField(column_name='Note', null=True)
    task = TextField(column_name='Task', null=True)

    class Meta:
        table_name = 'Users_notes'


class Lesson_start_end(BaseModel):
    """Таблица времени начала и конца пар"""
    lesson_number = IntegerField(column_name='LessonNumber')
    start_time = TimeField(column_name='StartTime')
    end_time = TimeField(column_name='EndTime')

    class Meta:
        table_name = 'Lesson_start_end'


class Users_communities(BaseModel):
    """Таблица выбранных пользователем сообществ"""
    user_id = IntegerField(column_name='UserId')
    community_id = IntegerField(column_name='CommunityId')

    class Meta:
        table_name = 'Users_communities'
