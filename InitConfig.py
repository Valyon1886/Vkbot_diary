from os import makedirs
from os.path import isfile, exists
from pathlib import Path
from json import dump, load


class Config:
    """Класс Config используется для создания и считывания файлов управления для бота."""
    _dir_name = "local_files"
    _config_name = "config.json"
    _config_dict = {}
    _users = "users_cache.json"
    users_dict = {}

    def __init__(self):
        """Создаёт файл конфигурации (если нету) и загружает его в память."""
        if not exists(self._dir_name):
            makedirs(self._dir_name)
        if isfile(Path(self._dir_name + '/' + self._config_name)):
            with open(file=Path(self._dir_name + '/' + self._config_name), mode="r", encoding="utf-8") as config_file:
                self._config_dict = load(config_file)
            print("Файл настроек загружен!")
        else:
            self._set_up_config()
        if exists(Path(self._dir_name + '/' + self._users)):
            with open(file=Path(self._dir_name + '/' + self._users), mode="r", encoding="utf-8") as users_file:
                self.users_dict = load(users_file)

    def get_dir_name(self):
        """Возвращает имя директории, где хранятся конфигурационные файлы."""
        return self._dir_name

    def _set_up_config(self):
        """Создаёт и заполняет конфигурационный файл бота."""
        print(f"Файл '{self._config_name}' не найден! Настраиваем новый!")
        self._set_token()
        self._set_user_info()

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
        if 'y' == input("Вы хотите использовать команду 'случайный мем'? (нужен логин и пароль пользователя) Y/n")\
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

    def save_users_dict(self):
        """Сохраняет словарь пользователей с их группами."""
        with open(file=Path(self._dir_name + '/' + self._users), mode="w", encoding="utf-8") as users_file:
            dump(self.users_dict, users_file)
