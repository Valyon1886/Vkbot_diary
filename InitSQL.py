from os import getcwd
from os.path import basename
from sys import exit, argv

from colorama import Fore, Style
from peewee import *

from InitConfig import Config

version = "0.3.3"


class InitSQL:
    """Класс для получения экземпляра соединения с подключенной базой данных"""
    _myDB = None

    @staticmethod
    def get_DB() -> MySQLDatabase:
        """Получение экземпляра соединения с подключенной базой данных"""
        if InitSQL._myDB is None and basename(getcwd()) != "docs":
            InitSQL._myDB = InitSQL._init_DB()
        return InitSQL._myDB

    @staticmethod
    def _init_DB() -> MySQLDatabase:
        """Инициализация соединения с базой данных и сохранение экземпляра"""
        if len(argv) > 1 and argv[1].lower() == "-v":
            print(version)
            exit(0)
        Config.read_config()
        database_config = Config.get_database_info()
        tries = 0
        total_tries = 3
        while True:
            tries += 1
            try:
                myDB = MySQLDatabase(host=database_config.get("host"),
                                     port=3306,
                                     user=database_config.get("user"),
                                     passwd=database_config.get("password"),
                                     database=database_config.get("database"))
                myDB.connect()
                break
            except OperationalError as Argument:
                if Argument.args[0] == 1049:
                    from pymysql import connect as mysqlconnector

                    conn = mysqlconnector(host=database_config.get("host"),
                                          user=database_config.get("user"),
                                          password=database_config.get("password"))
                    conn.cursor().execute(f'CREATE DATABASE {database_config.get("database")}')
                    conn.close()
                else:
                    message = "Ошибка " + ", ".join([str(x) for x in Argument.args])
                    if tries == total_tries:
                        exit(message)
                    else:
                        print(Fore.RED + message + f"\nОсталось попыток - {total_tries - tries}" + Style.RESET_ALL)
        return myDB
