from colorama import Fore, Style

from MySQLStorage import Weeks, Days, Subjects, Users_groups, Users_tasks, Lesson_start_end, Users_communities


class InitDatabase:
    """Класс для добавления начальных значений в базу данных"""

    @staticmethod
    def ensure_start_data_added() -> None:
        """Добавление начальных значений в базу данных"""
        InitDatabase._ensure_users_added()
        InitDatabase._ensure_communities_added()

    @staticmethod
    def _ensure_users_added() -> None:
        """Добавление начальных значений в таблицу 'Users_groups'"""
        users_data = [
            {'user_id': 283202201, 'group': "ИКБО-03-19"},
            {'user_id': 286251203, 'group': "ИКБО-06-19"},
            {'user_id': 248941603, 'group': "ИКБО-20-19"}
        ]
        if len([i for i in Users_groups.select().limit(1).execute()]) == 0:
            Users_groups.insert_many(users_data).execute()
            print(Fore.LIGHTBLUE_EX + "Начальные значения добавлены в таблицу 'Users'!" + Style.RESET_ALL)

    @staticmethod
    def _ensure_communities_added() -> None:
        """Добавление начальных значений в таблицу 'Users_communities'"""
        users_communities = [
            {'user_id': 92798890, 'community_id': 66678575},
            {'user_id': 92798890, 'community_id': 198870105},
            {'user_id': 283202201, 'community_id': 110713909},
            {'user_id': 283202201, 'community_id': 80463597}
        ]
        if len([i for i in Users_communities.select().limit(1).execute()]) == 0:
            Users_communities.insert_many(users_communities).execute()
            print(Fore.LIGHTBLUE_EX + "Начальные значения добавлены в таблицу 'Users_communities'!" + Style.RESET_ALL)
