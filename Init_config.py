from os.path import isfile
from json import dump, load


class Config:
    __config_name = "config.json"
    __config_dict = {}

    def __init__(self):
        if isfile(self.__config_name):
            with open(file=self.__config_name, mode="r", encoding="utf-8") as config_file:
                self.__config_dict = load(config_file)
            print("Файл настроек загружен!")
        else:
            self.__set_up_config()

    def __set_up_config(self):
        print(f"Файл '{self.__config_name}' не найден! Настраиваем новый!")
        self.__set_token()

        with open(file=self.__config_name, mode="w", encoding="utf-8") as config_file:
            dump(self.__config_dict, config_file, indent=2)
        print("Файл настроек сохранён!")

    def __set_token(self):
        self.__config_dict["token"] = input("Введите токен vk бота: ")

    def get_token(self):
        return self.__config_dict["token"]
