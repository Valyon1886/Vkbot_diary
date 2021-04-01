from MySQLStorage import Weeks, Days_Lessons, Schedule_of_subject, Users, Users_notes


class InitDatabase:
    """Класс для добавления тестовых значений в базу данных"""
    @staticmethod
    def ensure_start_data_added():
        """Добавление тестовых значений в базу данных"""
        InitDatabase._ensure_users_added()
        InitDatabase._ensure_notes_added()

    @staticmethod
    def _ensure_users_added():
        """Добавление тестовых значений в таблицу 'Users'"""
        users_data = [
            {'user_id': 283292203, 'group': "ИКБО-03-19"},
            {'user_id': 286251203, 'group': "ИКБО-06-19"},
            {'user_id': 248941603, 'group': "ИКБО-20-19"}
        ]
        if len([i for i in Users.select().limit(1).execute()]) == 0:
            Users.insert_many(users_data).execute()
            print("Тестовые значения добавлены в таблицу 'Users'!")

    @staticmethod
    def _ensure_notes_added():
        """Добавление тестовых значений в таблицу 'Users_notes'"""
        pass
