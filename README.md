<p align="center">
   <img src="bot.ico">
</p>

<h1 align="center">
   Vkbot diary
</h1>

ВК бот для получения расписания с учётом пользовательских задач.

## Команды
* `XXXX-XX-XX` - Запоминает введённую группу (вводится группа по паттерну, например ИКБО-03-19).
* `Расписание` - Выводит клавиатуру с выбором подкоманды.
  * `На сегодня` - Выводит расписание и задачи (если есть) на сегодня.
  * `На завтра` - Выводит расписание и задачи (если есть) на завтра.
  * `На эту неделю` - Выводит расписание и задачи (если есть) на эту неделю.
  * `На следующую неделю` - Выводит расписание и задачи (если есть) на следующую неделю.
  * `Какая неделя?` - Выводит номер учебной недели.
  * `Какая группа?` - Выводит группу пользователя.
* `Задачи` - Выводит клавиатуру с выбором подкоманды.
  * `Добавить задачу` - Добавляет введённую задачу и закрепляет её за данным пользователем.
  * `Изменить задачу` - Изменяет введённую задачу, принадлежащую данному пользователю.
  * `Удалить задачу` - Удаляет введённую задачу, принадлежащую данному пользователю.
* `Мем` - Выводит клавиатуру с выбором подкоманды.
  * `Случайный мем` - Отправляет с шансом 75% случайный мем (картинку) из случайно выбранного из списка сообщества.
  * `Мои сообщества` - Выводит список пользовательских сообществ.
  * `Добавить сообщество` - Добавляет сообщества в виде url ссылок из текста следующего сообщения пользователя.
  * `Удалить сообщество` - Удаляет сообщества в виде url ссылок или номеров сообществ из текста следующего сообщения пользователя.

**Примечание:** Также доступен голосовой ввод этих команд на русском языке.

## Зависимости
* [Python 3.8](https://www.python.org/downloads/)
* [mySQL](https://www.mysql.com/)
* [ffmpeg](https://ffmpeg.org/download.html)
  * Установка под Windows [(на английском)](https://www.wikihow.com/Install-FFmpeg-on-Windows)
    [(на русском)](https://ru.wikihow.com/установить-программу-FFmpeg-в-Windows)
  * Установка под Ubuntu - выполнить команду `sudo apt-get install ffmpeg`, если не может поставить, то выполнить сначала команду `sudo apt-get update`
____________
> Библиотеки для Python: 
* [vk_api](https://github.com/python273/vk_api) - библиотека для работы бота с ВК.
* [xlrd](https://github.com/python-excel/xlrd) - библиотека для парсинга .xlsx-файлов.
* [Sphinx](https://github.com/sphinx-doc/sphinx) - библиотека для генерации документации.
* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/) - библиотека для парсинга html страниц.
* [PyMySQL](https://github.com/PyMySQL/PyMySQL) - библиотека, содержащая клиент для базы MySQL.
* [cryptography](https://github.com/pyca/cryptography) - библиотека для шифрования пароля при установлении соединения с базой данных.
* [peewee](https://github.com/coleifer/peewee) - библиотека для работы с базой данных через удобные классы (ORM).
* [pyinstaller](https://github.com/pyinstaller/pyinstaller) - библиотека для сборки проекта в исполняемый файл.
* [SpeechRecognition](https://github.com/Uberi/speech_recognition) - библиотека распознавания голосовых сообщений.
* [colorama](https://github.com/tartley/colorama) - библиотека для цветного вывода сообщений в консоль бота.
* [requests](https://github.com/psf/requests) - библиотека для скачивания файлов с сайта.
* [dateparser](https://github.com/scrapinghub/dateparser) - библиотека для парсинга текстовой даты от пользователя на любом языке в datetime объект.
* [dateutil](https://github.com/paxan/python-dateutil) - библиотека, расширяющая возможности стандартного модуля datetime, в частности улучшает парсинг даты из строки.

## Установка зависимостей
Надо выполнить команду ниже в командной строке или терминале, находясь в корневой папке проекта.
```
pip install -r requirements.txt
```
**Примечание:** Вы должны иметь [requirements.txt](requirements.txt) в корневой папке проекта.

## Сборка

### Сборка приложения
Надо выполнить команду `make` в командной строке или терминале, находясь в корневой папке проекта. 
По окончанию сборки в корневой папке проекта создастся папка `/build_dist`, в ней будет лежать собранный исполняемый файл. 
<!---->
**Примечание:** Для сборки есть makefile, но если вы не хотите использовать утилиту 
[make](https://www.gnu.org/software/make/), то для Windows есть .bat файл.

### Сборка документации
Введите, находясь в [/docs](docs), в командной строке `make html`.
<!---->
Для чтения документации надо открыть index.html по пути docs/build/html/ в любом браузере.

## Запуск
Запустить исполняемый файл, который находится в папке `/build_dist`. Но это уже самодостаточная сборка приложения, 
поэтому оно будет работать в любой директории.
<!---->
Или исполнить основной файл `VkBotDiary.py` через команду `python VkBotDiary.py` или если в Linux не работает эта команда, 
то тогда через эту - `python3 VkBotDiary.py`, предварительно установив все зависимости.

## Docker

### Готовый образ
[Страница контейнера бота](https://hub.docker.com/r/druzai/vkbotdiary)
<!---->
Для развёртывания готового образа с ботом и базой данных, находясь в корневой папке проекта, надо:
* В файле [docker-compose.yml](docker-compose.yml) указать свои значения переменных окружения:
  * `WAIT_HOSTS`: указывается контейнер с названием базы данных mySQL и портом для прослушивания через двоеточие, **менять если вы поменяли имя контейнера базы данных**
  * `WAIT_HOSTS_TIMEOUT`: время ожидания проверки подключения к базе данных mySQL в секундах до неудачи, **можно не менять**
  * `WAIT_SLEEP_INTERVAL`: время бездействия проверки подключения к базе данных mySQL в секундах до следующей попытки, **можно не менять**
  * `WAIT_HOST_CONNECT_TIMEOUT`: время пингования подключения к базе данных mySQL в секундах, **можно не менять**
  * `BOT_TOKEN`: токен вк бота сообщества, **обязательно вставить!**
  * `BOT_USER_LOGIN`: логин пользователя, через которого работают команды связанные с мемами, ***по желанию*, можно не указывать (удалить из списка)**
  * `BOT_USER_PASSWORD`: пароль пользователя, через которого работают команды связанные с мемами, ***по желанию*, можно не указывать (удалить из списка)**
  * `MYSQL_HOST`: имя контейнера базы данных mySQL, **менять если вы поменяли имя контейнера базы данных**
  * `MYSQL_USER`: имя пользователя базы данных mySQL, **менять если вы хотите использовать другого пользователя вместо `root` для базы данных**
  * `MYSQL_PASSWORD`: пароль пользователя базы данных mySQL, **менять если вы хотите используете другой пароль пользователя или другого пользователя для базы данных**
  * `MYSQL_DATABASE`: имя базы данных в mySQL, где будут храниться таблицы для бота, **можно указать какое хотите название**
  * `BOT_AWAIT_TIME`: время в секундах на ожидание перед очередным обновлением файлов расписания, **указать какое хотите значение**
* Для запуска контейнера — команду `docker-compose -p "my-app" up` (`my-app` - имя контейнера)
<!---->
**Примечание:** Если в строке, которую выводите в значения переменных окружения, есть знак доллара, то его надо экранировать долларом. Пример: было так - `"fung$gbiobm"`, а надо так - `"fung$$gbiobm"`.

### Сборка образа своими руками
Но если вы хотите сделать собственный образ и запустить его с базой данных, а не скачивать готовый, то в корневой папке проекта должно быть 2 файла: Dockerfile и изменённый docker-compose.yml
<!---->
**Dockerfile**
```dockerfile
FROM python:3.8.5

# copy bot files and its requirements
WORKDIR /VkBotDiary/
ADD *.py /VkBotDiary/
ADD requirements.txt /VkBotDiary/

# install requirements
RUN pip install -r requirements.txt

# install ffmpeg
RUN apt-get update
RUN apt-get -y install ffmpeg

# Add docker-compose-wait tool
ENV WAIT_VERSION 2.7.3
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait ./wait-script
RUN chmod 775 ./wait-script
```
**docker-compose.yml**
```dockerfile
version: '3.6'

services:
  db:
    image: mysql:8.0.23
    container_name: db
    restart: always
    environment:
        MYSQL_ROOT_PASSWORD: root_password
        MYSQL_ROOT_HOST: "%"
        MYSQL_USER: test_user
        MYSQL_PASSWORD: test_password
    ports:
      - "3306:3306"
  vkbotdiary:
    build: ./
    command: sh -c "./wait-script && python ./VkBotDiary.py"
    restart: always
    depends_on:
      - db
    links:
      - db
    environment:
        WAIT_HOSTS: "db:3306"
        WAIT_HOSTS_TIMEOUT: 300
        WAIT_SLEEP_INTERVAL: 5
        WAIT_HOST_CONNECT_TIMEOUT: 10
        BOT_TOKEN: "your-vk-bot-token-here"
        BOT_USER_LOGIN: "vk-user-login"
        BOT_USER_PASSWORD: "vk-user-password"
        MYSQL_HOST: "db"
        MYSQL_USER: "root"
        MYSQL_PASSWORD: "root_password"
        MYSQL_DATABASE: "Your-Database"
        BOT_AWAIT_TIME: 3600
```
Настройка значений переменных окружения, сборка и запуск контейнера аналогична описанию выше.

## Протестированные платформы
* Windows 7 или выше (32/64 бит)
* Linux (Ubuntu/Debian/CentOS)