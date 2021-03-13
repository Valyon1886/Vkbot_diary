from os import makedirs
from os.path import isfile, exists
from pathlib import Path
from json import dump, load


class Config:
    _dir_name = "local_files"
    _config_name = "config.json"
    _config_dict = {}
    _users = "users_cache.json"
    users_dict = {}

    def __init__(self):
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

    def _set_up_config(self):
        print(f"Файл '{self._config_name}' не найден! Настраиваем новый!")
        self._set_token()

        with open(file=self._config_name, mode="w", encoding="utf-8") as config_file:
            dump(self._config_dict, config_file, indent=2)
        print("Файл настроек сохранён!")

    def _set_token(self):
        self._config_dict["token"] = input("Введите токен vk бота: ")

    def get_token(self):
        return self._config_dict["token"]

    def save_users_dict(self):
        with open(file=Path(self._dir_name + '/' + self._users), mode="w", encoding="utf-8") as users_file:
            dump(self.users_dict, users_file)
