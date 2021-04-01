from peewee import *
from InitSQL import InitSQL


class BaseModel(Model):
    """Базовая модель таблицы для базы данной"""

    class Meta:
        database = InitSQL.get_DB()


class Schedule_of_subject(BaseModel):
    """Таблица информации о каждой паре"""
    schedule_id = AutoField(column_name='ScheduleId')
    time_lesson = TimeField(column_name='TimeLesson')
    subject_task = TextField(column_name='Subject/Task')
    teacher = TextField(column_name='Teacher')
    class_number = TextField(column_name='ClassNumber')
    link = TextField(column_name='Link')

    class Meta:
        table_name = 'Schedule_of_day'


class Days_Lessons(BaseModel):
    """Таблица пар для дней"""
    day_lesson_id = AutoField(column_name='DayLessonId')
    day_of_week = TextField(column_name='DayOfWeek')
    schedule_of_subject = ForeignKeyField(Schedule_of_subject, to_field='schedule_id')

    class Meta:
        table_name = 'Days'


class Weeks(BaseModel):
    """Таблица дней и пар для выбранной группы и нечётной/чётной недели"""
    week_id = AutoField(column_name='WeekId')
    group = TextField(column_name='Group')
    even = BooleanField(column_name='Even')
    day_lesson = ForeignKeyField(Days_Lessons, to_field='day_lesson_id')

    class Meta:
        table_name = 'Weeks'


class Users(BaseModel):
    """Таблица выбранных групп для каждого пользователя"""
    user_id = IntegerField(column_name='UserId')
    group = TextField(column_name='Group')

    class Meta:
        table_name = 'Users'


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


'''
class Role(BaseModel):
    """ Field Types """
    role_id = AutoField(column_name='RoleId')
    rolename = CharField(25)

    class Meta:
        db_table = 'roles'


class User(BaseModel):
    """ Field Types """
    user_id = PrimaryKeyField()
    username = CharField(25)
    role = ForeignKeyField(Role, to_field="role_id")

    class Meta:
        db_table = 'users'
'''

if __name__ == '__main__':
    print("IDDKD")
    # datetime.datetime.strptime("12-40", '%H-%M').time()
    # User.create(username="Lol2", role=Role.create(rolename="Name2"))
    #
    # for user in User.select().where(User.user_id == 1):
    #     print(user.username)
    #     print(user.role.rolename)
    # artists_data = [
    #     {'name': '1-qаыаed'},
    #     {'name': '2-qasggsg'},
    #     {'name': '3-qaswed'},
    #     {'name': '41-yhnbgt'},
    #     {'name': '5-yhnbgsght'},
    #     {'name': '14-yhgsgsnbgt'}
    # ]
    # # Artist.insert_many(artists_data).execute()
    #
    # cur_query = Artist.select().where("1" in Artist.name).limit(10).order_by(Artist.artist_id.desc())
    # for item in cur_query.dicts().execute():
    #     print('artist: ', item)
    # MySQL()
