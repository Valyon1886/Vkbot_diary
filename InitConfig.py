from os import makedirs
from os.path import isfile, exists
from pathlib import Path
from json import dump, load

from colorama import Fore, Style


class Config:
    """Класс Config используется для создания и считывания файлов управления для бота."""
    _dir_name = "local_files"
    _config_name = "config.json"
    _config_dict = {}

    @staticmethod
    def read_config():
        """Создаёт файл конфигурации (если нету) и загружает его в память."""
        file_exists = False
        if not exists(Config._dir_name):
            makedirs(Config._dir_name)
        first = len(Config._config_dict) == 0
        if isfile(Path(Config._dir_name + '/' + Config._config_name)):
            with open(file=Path(Config._dir_name + '/' + Config._config_name), mode="r",
                      encoding="utf-8") as config_file:
                Config._config_dict = load(config_file)
            file_exists = True
        Config._set_up_config(file_exists, first)

    @staticmethod
    def save_config():
        """Сохраняет файл конфигурации"""
        with open(file=Path(Config._dir_name + '/' + Config._config_name), mode="w", encoding="utf-8") as config_file:
            dump(Config._config_dict, config_file, indent=2)

    @staticmethod
    def get_dir_name() -> str:
        """Возвращает имя директории, где хранятся конфигурационные файлы."""
        return Config._dir_name

    @staticmethod
    def _set_up_config(file_exists=False, first=False):
        """Создаёт и заполняет конфигурационный файл бота."""
        changes_made = False
        if first:
            if not file_exists:
                print(Fore.YELLOW + f"Файл '{Config._config_name}' не найден! Настраиваем новый!" + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + f"Файл '{Config._config_name}' найден!" + Style.RESET_ALL)

        if Config._config_dict.get("token", None) is None:
            changes_made = True
            Config._set_token()

        if Config._config_dict.get("user_login", None) is None or \
                Config._config_dict.get("user_password", None) is None:
            changes_made = True
            Config._set_user_info()

        if Config._config_dict.get("mysqldb", None) is None:
            changes_made = True
            Config._set_database_info()

        if Config._config_dict.get("init_database", None) is None:
            changes_made = True
            Config._set_init_database()

        if Config._config_dict.get("schedule_info", None) is None:
            changes_made = True
            Config._config_dict["schedule_info"] = dict()

        if Config._config_dict.get("await_time", None) is None:
            changes_made = True
            Config._set_await_time()

        if changes_made:
            Config.save_config()
        if not file_exists:
            print(Fore.GREEN + "Файл настроек сохранён!" + Style.RESET_ALL)

    @staticmethod
    def _set_token():
        """Устанавливает токен для бота"""
        Config._config_dict["token"] = input("Введите токен vk бота: ")

    @staticmethod
    def get_token() -> str:
        """Возвращает токен для бота"""
        return Config._config_dict["token"]

    @staticmethod
    def _set_user_info():
        """Устанавливает логин и пароль пользователя для бота."""
        if 'y' == input("Вы хотите использовать команду 'случайный мем'? (нужен логин и пароль пользователя) Y/n\n") \
                .lower():
            Config._config_dict["user_login"] = input("Введите логин пользователя: ")
            Config._config_dict["user_password"] = input("Введите пароль пользователя: ")
        else:
            Config._config_dict["user_login"] = None
            Config._config_dict["user_password"] = None

    @staticmethod
    def get_user_info() -> tuple or None:
        """Возвращает логин и пароль пользователя для бота."""
        if Config._config_dict.get("user_login", None) and Config._config_dict.get("user_password", None):
            return Config._config_dict.get("user_login", None), Config._config_dict.get("user_password", None)
        else:
            return None

    @staticmethod
    def _set_database_info():
        """Устанавливает информацию о подключении к базе данных"""
        myDB = {}
        if 'y' == input("Ваша mysql находится на localhost (вариант для docker-образа)? Y/n\n"):
            myDB = {
                "host": "localhost",
                "user": "root",
                "password": "root",
                "database": "Storage"
            }
            print(Fore.LIGHTGREEN_EX + "Настройки взяты по умолчанию:\n" + str(myDB) + Style.RESET_ALL)
        else:
            myDB["host"] = input("Введите хост базы данных: ")
            myDB["user"] = input("Введите логин пользователя для подключения к базе данных: ")
            myDB["password"] = input("Введите пароль пользователя для подключения к базе данных: ")
            myDB["database"] = "Storage"

        Config._config_dict["mysqldb"] = myDB

    @staticmethod
    def get_database_info() -> dict:
        """Возвращает информацию о подключении к базе данных"""
        return Config._config_dict["mysqldb"]

    @staticmethod
    def _set_init_database():
        """Устанавливает надо ли добавлять тестовые значения в базу данных в пустые таблицы"""
        Config._config_dict["init_database"] = 'y' == input("Добавлять тестовые значения в базу данных в пустые " +
                                                            "таблицы? Y/n\n").lower()

    @staticmethod
    def get_init_database() -> bool:
        """Возвращает информацию о необходимости добавлений тестовых значений в базу данных"""
        return Config._config_dict["init_database"]

    @staticmethod
    def set_schedule_info(schedule_info_dict: dict):
        """Сохраняет словарь: ключ - имя скачанного файла расписания, значение - хеш-значение (md5) этого файла"""
        Config._config_dict["schedule_info"] = schedule_info_dict

    @staticmethod
    def get_schedule_info() -> dict:
        """Возвращает словарь с скачаными файлами и их хеш-значениями (md5)"""
        return Config._config_dict["schedule_info"]

    @staticmethod
    def _set_await_time():
        """Сохраняет время ожидания перед проверкой расписания в секундах"""
        Config._config_dict["await_time"] = int(input("Введите сколько секунд бот будет ожидать" +
                                                      " перед проверкой расписания с сайта МИРЭА: "))

    @staticmethod
    def get_await_time() -> int:
        """Возвращает время ожидания перед проверкой расписания в секундах"""
        return Config._config_dict["await_time"]
