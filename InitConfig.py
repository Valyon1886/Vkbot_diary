import datetime
from json import dump, load
from os import makedirs, environ
from os.path import isfile, exists
from pathlib import Path
from sys import exit

from colorama import Fore, Style, init as c_init
from dateparser import parse as date_parse


class Config:
    """Класс Config используется для создания и считывания файлов управления для бота."""
    _dir_name = "local_files"
    _config_name = "config.json"
    _config_dict = {}
    _weeks_times = {}
    _runned_from_docker = False

    @staticmethod
    def read_config() -> None:
        """Создаёт файл конфигурации (если нету) и загружает его в память"""
        c_init()
        file_exists = False
        if not exists(Config._dir_name):
            makedirs(Config._dir_name)
        first = len(Config._config_dict) == 0
        if isfile(Path(Config._dir_name + '/' + Config._config_name)):
            with open(file=Path(Config._dir_name + '/' + Config._config_name), mode="r", encoding="utf-8") as conf_file:
                Config._config_dict = load(conf_file)
            file_exists = True
        Config._set_up_config(file_exists, first)

    @staticmethod
    def save_config() -> None:
        """Сохраняет файл конфигурации"""
        try:
            with open(file=Path(Config._dir_name + '/' + Config._config_name), mode="w", encoding="utf-8") as conf_file:
                dump(Config._config_dict, conf_file, indent=2, ensure_ascii=False)
        except FileNotFoundError:
            Config.save_config()

    @staticmethod
    def get_dir_name() -> str:
        """Возвращает имя директории, где хранятся конфигурационные файлы

        Return
        ----------
        dir_name: dict
            имя директории, где хранятся конфигурационные файлы
        """
        return Config._dir_name

    @staticmethod
    def _set_up_config(file_exists=False, first=False) -> None:
        """Проверяет и заполняет (если нет каких-то ключей) конфигурационный файл бота

        Parameters
        ----------
        file_exists: bool
            существует ли конфигурационный файл
        first: bool
            Первый ли раз вызывается данная функция
        """
        env_vars = {}
        for var in ["BOT_TOKEN", "BOT_USER_LOGIN", "BOT_USER_PASSWORD", "START_WEEK", "PRE_EXAM_WEEK",
                    "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE", "MYSQL_HOST", "BOT_AWAIT_TIME"]:
            try:
                var_value = environ[var]
                env_vars[var] = var_value
                if not Config._runned_from_docker:
                    Config._runned_from_docker = True
            except KeyError:
                pass

        changes_made = False
        if first:
            if not file_exists:
                print(Fore.YELLOW + f"Файл '{Config._config_name}' не найден! Настраиваем новый!" + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + f"Файл '{Config._config_name}' найден!" + Style.RESET_ALL)

        if Config._config_dict.get("token", None) is None:
            changes_made = True
            Config._set_token(token=env_vars.get("BOT_TOKEN", None))

        if Config._config_dict.get("user_login", None) is None or \
                Config._config_dict.get("user_password", None) is None:
            changes_made = True
            Config._set_user_info(user_login=env_vars.get("BOT_USER_LOGIN", None),
                                  user_password=env_vars.get("BOT_USER_PASSWORD", None))

        if Config._config_dict.get("weeks_times", None) is None:
            changes_made = True
            Config._set_weeks_info(start_week=env_vars.get("START_WEEK", None),
                                   pre_exam_week=env_vars.get("PRE_EXAM_WEEK", None))

        for k, v in Config._config_dict["weeks_times"].items():
            if k == "start_week":
                # Get Monday 00:00
                Config._weeks_times[k] = date_parse(v) - datetime.timedelta(days=date_parse(v).weekday() % 7)
                Config._weeks_times[k] = datetime.datetime.combine(Config._weeks_times[k].date(),
                                                                   datetime.datetime.min.time())
            else:
                # Get Sunday 23:59
                Config._weeks_times[k] = date_parse(v) - datetime.timedelta(days=date_parse(v).isoweekday() % 7) + \
                                         datetime.timedelta(days=7)
                Config._weeks_times[k] = datetime.datetime.combine(Config._weeks_times[k].date(),
                                                                   datetime.datetime.max.time())

        if Config._config_dict.get("mysqldb", None) is None:
            changes_made = True
            Config._set_database_info(mysql_host=env_vars.get("MYSQL_HOST", None),
                                      mysql_user=env_vars.get("MYSQL_USER", None),
                                      mysql_password=env_vars.get("MYSQL_PASSWORD", None),
                                      mysql_database=env_vars.get("MYSQL_DATABASE", None))

        if Config._config_dict.get("init_database", None) is None:
            changes_made = True
            Config._set_init_database()

        if Config._config_dict.get("schedule_info", None) is None:
            changes_made = True
            Config._config_dict["schedule_info"] = dict()

        if Config._config_dict.get("await_time", None) is None:
            changes_made = True
            Config._set_await_time(bot_await_time=env_vars.get("BOT_AWAIT_TIME", None))

        if changes_made:
            Config.save_config()
        if not file_exists:
            print(Fore.GREEN + "Файл настроек сохранён!" + Style.RESET_ALL)

    @staticmethod
    def _set_token(token=None) -> None:
        """Устанавливает токен для бота

        Parameters
        ----------
        token: str or None
            токен бота в виде строки или None
        """
        if Config._runned_from_docker:
            if token is None:
                exit("Нету токена бота в переменных окружения!")
            else:
                Config._config_dict["token"] = token
        else:
            Config._config_dict["token"] = input("Введите токен vk бота: ")

    @staticmethod
    def get_token() -> str:
        """Возвращает токен для бота

        Return
        ----------
        token: str
            токен для бота
        """
        return Config._config_dict["token"]

    @staticmethod
    def _set_user_info(user_login=None, user_password=None) -> None:
        """Устанавливает логин и пароль пользователя для бота

        Parameters
        ----------
        user_login: str or None
            логин пользователя для бота
        user_password: str or None
            пароль пользователя для бота
        """
        if Config._runned_from_docker:
            if any([i is None for i in [user_login, user_password]]):
                Config._config_dict["user_login"] = None
                Config._config_dict["user_password"] = None
            else:
                Config._config_dict["user_login"] = user_login
                Config._config_dict["user_password"] = user_password
        else:
            if 'y' == input("Вы хотите использовать команду 'случайный мем'?"
                            " (нужен логин и пароль пользователя) Y/n\n").lower():
                Config._config_dict["user_login"] = input("Введите логин пользователя: ")
                Config._config_dict["user_password"] = input("Введите пароль пользователя: ")
            else:
                Config._config_dict["user_login"] = None
                Config._config_dict["user_password"] = None

    @staticmethod
    def get_user_info() -> tuple or None:
        """Возвращает логин и пароль пользователя для бота

        Return
        ----------
        user_login: str or None
            логин пользователя для бота
        user_password: str or None
            пароль пользователя для бота
        """
        if Config._config_dict.get("user_login", None) and Config._config_dict.get("user_password", None):
            return Config._config_dict.get("user_login", None), Config._config_dict.get("user_password", None)
        else:
            return None

    @staticmethod
    def _set_weeks_info(start_week=None, pre_exam_week=None):
        """Устанавливает даты начала семестра и зачётной недели для бота

        Parameters
        ----------
        start_week: str or None
            дата начала семестра
        pre_exam_week: str or None
            дата зачётной недели
        """
        weeks_times = {}
        if Config._runned_from_docker:
            if any([i is None for i in [start_week, pre_exam_week]]):
                exit("Нету даты начала семестра и даты зачётной недели семестра в переменных окружения!")
            else:
                weeks_times["start_week"] = start_week
                weeks_times["pre_exam_week"] = pre_exam_week
        else:
            while all(weeks_times.get(j, None) is None for j in ["start_week", "pre_exam_week"]):
                for i in ["start_week", "pre_exam_week"]:
                    if weeks_times.get(i, None) is None:
                        datetime_text = input(
                            f"Введите дату {'начала семестра' if i == 'start_week' else 'зачётной недели семестра'}: ")
                        print(f"Дата {'начала семестра' if i == 'start_week' else 'зачётной недели семестра'} "
                              f"поставлена на {date_parse(datetime_text).strftime('%d.%m.%Y %H:%M')}. Продолжить? Y/n")
                        if input().lower() == "y":
                            weeks_times[i] = datetime_text

        Config._config_dict["weeks_times"] = weeks_times

    @staticmethod
    def get_weeks_info() -> dict:
        """Возвращает даты начала семестра и зачётной недели для бота

        Return
        ----------
        weeks: dict
            словарь с датами начала семестра и зачётной недели в виде datetime объекта
        """
        return Config._weeks_times

    @staticmethod
    def _set_database_info(mysql_host=None, mysql_user=None, mysql_password=None, mysql_database=None) -> None:
        """Устанавливает информацию о подключении к базе данных

        Parameters
        ----------
        mysql_host: str or None
            ip адрес базы данных
        mysql_user: str or None
            пароль пользователя базы данных
        mysql_password: str or None
            логин пользователя базы данных
        mysql_database: str or None
            пароль пользователя базы данных
        """
        myDB = {}
        if Config._runned_from_docker:
            if any([i is None for i in [mysql_user, mysql_password, mysql_host]]):
                exit("Нету логина, пароля пользователя и хоста (названия образа) базы данных "
                     "для подключения бота к базе данных в переменных окружения!")
            else:
                myDB["host"] = mysql_host
                myDB["user"] = mysql_user
                myDB["password"] = mysql_password
                myDB["database"] = mysql_database if mysql_database else "Storage"
        else:
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
                myDB["database"] = input("Введите название базы данных: ")

        Config._config_dict["mysqldb"] = myDB

    @staticmethod
    def get_database_info() -> dict:
        """Возвращает информацию о подключении к базе данных

        Return
        ----------
        mysqldb: dict
            словарь с параметрами о подключении к базе данных
        """
        return Config._config_dict["mysqldb"]

    @staticmethod
    def _set_init_database() -> None:
        """Устанавливает надо ли добавлять тестовые значения в базу данных в пустые таблицы"""
        if Config._runned_from_docker:
            Config._config_dict["init_database"] = False
        else:
            Config._config_dict["init_database"] = 'y' == input("Добавлять тестовые значения в базу данных в пустые " +
                                                                "таблицы? Y/n\n").lower()

    @staticmethod
    def get_init_database() -> bool:
        """Возвращает информацию о необходимости добавлений тестовых значений в базу данных

        Return
        ----------
        init_database: bool
            необходимость добавлений тестовых значений в базу данных
        """
        return Config._config_dict["init_database"]

    @staticmethod
    def set_schedule_info(schedule_info_dict: dict) -> None:
        """Сохраняет словарь: ключ - имя скачанного файла расписания, значение - хеш-сумма (md5) этого файла

        Parameters
        ----------
        schedule_info_dict: dict
            словарь с названиями распарсенных файдов расписания и их хеш-суммами
        """
        Config._config_dict["schedule_info"] = schedule_info_dict

    @staticmethod
    def get_schedule_info() -> dict:
        """Возвращает словарь с названиями распарсенных файдов расписания и их хеш-суммами (md5)

        Return
        ----------
        schedule_info: dict
            словарь с названиями распарсенных файдов расписания и их хеш-суммами
        """
        return Config._config_dict["schedule_info"]

    @staticmethod
    def _set_await_time(bot_await_time=None) -> None:
        """Сохраняет время ожидания перед проверкой расписания в секундах

        Parameters
        ----------
        bot_await_time: int ot None
            время ожидания перед проверкой расписания в секундах
        """
        if Config._runned_from_docker:
            if bot_await_time is None:
                Config._config_dict["await_time"] = 10800
                print("Не было указано время ожидания! Было выставлено время ожидания в 3 часа!")
            else:
                try:
                    Config._config_dict["await_time"] = int(bot_await_time)
                except ValueError:
                    Config._config_dict["await_time"] = 10800
                    print("Время ожидания указано не верно (невозможно привести к int)! "
                          "Было выставлено время ожидания в 3 часа!")
        else:
            Config._config_dict["await_time"] = int(input("Введите сколько секунд бот будет ожидать" +
                                                          " перед проверкой расписания с сайта МИРЭА: "))

    @staticmethod
    def get_await_time() -> int:
        """Возвращает время ожидания перед проверкой расписания в секундах

        Return
        ----------
        await_time: int
            время ожидания перед проверкой расписания в секундах
        """
        return Config._config_dict["await_time"]
