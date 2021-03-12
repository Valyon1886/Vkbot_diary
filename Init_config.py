from os.path import isfile
from json import dump, load


class Config:
    config_name = "config.json"
    config_dict = {}

    def __init__(self):
        if isfile(self.config_name):
            with open(file=self.config_name, mode="r", encoding="utf-8") as config_file:
                self.config_dict = load(config_file)
            print("Файл настроек загружен!")
        else:
            self.set_up_config()

    def set_up_config(self):
        print(f"Файл '{self.config_name}' не найден! Настраиваем новый!")
        self.set_token()

        with open(file=self.config_name, mode="w", encoding="utf-8") as config_file:
            dump(self.config_dict, config_file, indent=2)
        print("Файл настроек сохранён!")

    def set_token(self):
        self.config_dict["token"] = input("Введите токен vk бота: ")

    def get_token(self):
        return self.config_dict["token"]
