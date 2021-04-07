from os import makedirs
from os.path import isfile, exists
from pathlib import Path
from json import dump, load


class Config:
    """Класс Config используется для создания и считывания файлов управления для бота."""
    _dir_name = "local_files"
    _config_name = "config.json"
    _config_dict = {}

    def __init__(self):
        """Создаёт файл конфигурации (если нету) и загружает его в память."""
        if not exists(self._dir_name):
            makedirs(self._dir_name)
        if isfile(Path(self._dir_name + '/' + self._config_name)):
            with open(file=Path(self._dir_name + '/' + self._config_name), mode="r", encoding="utf-8") as config_file:
                self._config_dict = load(config_file)
        else:
            self._set_up_config()

    def get_dir_name(self):
        """Возвращает имя директории, где хранятся конфигурационные файлы."""
        return self._dir_name

    def _set_up_config(self):
        """Создаёт и заполняет конфигурационный файл бота."""
        print(f"Файл '{self._config_name}' не найден! Настраиваем новый!")
        self._set_token()
        self._set_user_info()
        self._set_database_info()
        self._set_init_database()

        with open(file=Path(self._dir_name + '/' + self._config_name), mode="w", encoding="utf-8") as config_file:
            dump(self._config_dict, config_file, indent=2)
        print("Файл настроек сохранён!")

    def _set_token(self):
        """Устанавливает токен для бота"""
        self._config_dict["token"] = input("Введите токен vk бота: ")

    def get_token(self):
        """Возвращает токен для бота"""
        return self._config_dict["token"]

    def _set_user_info(self):
        """Устанавливает логин и пароль пользователя для бота."""
        if 'y' == input("Вы хотите использовать команду 'случайный мем'? (нужен логин и пароль пользователя) Y/n\n") \
                .lower():
            self._config_dict["user_login"] = input("Введите логин пользователя: ")
            self._config_dict["user_password"] = input("Введите пароль пользователя: ")
        else:
            self._config_dict["user_login"] = None
            self._config_dict["user_password"] = None

    def get_user_info(self):
        """Возвращает логин и пароль пользователя для бота."""
        if self._config_dict.get("user_login", None) and self._config_dict.get("user_password", None):
            return self._config_dict.get("user_login", None), self._config_dict.get("user_password", None)
        else:
            return None

    def _set_database_info(self):
        """Устанавливает информацию о подключении к базе данных"""
        myDB = {}
        if 'y' == input("Ваша mysql находится на localhost (вариант для docker-образа)? Y/n\n"):
            myDB = {
                "host": "localhost",
                "user": "root",
                "password": "root",
                "database": "Storage"
            }
            print("Настройки взяты по умолчанию:\n" + str(myDB))
        else:
            myDB["host"] = input("Введите хост базы данных: ")
            myDB["user"] = input("Введите логин пользователя для подключения к базе данных: ")
            myDB["password"] = input("Введите пароль пользователя для подключения к базе данных: ")
            myDB["database"] = "Storage"

        self._config_dict["mysqldb"] = myDB

    def get_database_info(self):
        """Возвращает информацию о подключении к базе данных"""
        return self._config_dict["mysqldb"]

    def _set_init_database(self):
        """Устанавливает надо ли добавлять тестовые значения в базу данных в пустые таблицы"""
        self._config_dict["init_database"] = 'y' == input("Добавлять тестовые значения в базу данных в пустые " +
                                                          "таблицы? Y/n\n").lower()

    def get_init_database(self):
        """Возвращает информацию о необходимости добавлений тестовых значений в базу данных"""
        return self._config_dict["init_database"]
