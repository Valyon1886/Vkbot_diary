<p align="center">
   <img src="bot.ico">
</p>

<h1 align="center">
   Vkbot diary
</h1>

ВК бот для получения расписания с учётом пользовательских заметок.

## Команды
* `Расписание` - Выводит клавиатуру с выбором подкоманды
  * `На сегодня` - Выводит расписание и заметки (если есть) на сегодня
  * `На завтра` - Выводит расписание и заметки (если есть) на завтра
  * `На эту неделю` - Выводит расписание и заметки (если есть) на эту неделю
  * `На следующую неделю` - Выводит расписание и заметки (если есть) на следующую неделю
  * `Какая неделя?` - Выводит номер учебной недели
  * `Какая группа?` - Выводит группу пользователя
* `XXXX-XX-XX` - Запоминает введённую группу (вводится группа по паттерну, например ИКБО-03-19)
* `Мем` - Выводит клавиатуру с выбором подкоманды
  * `Случайный мем` - Отправляет с шансом 75% случайный мем (картинку) из случайно выбранного из списка сообщества
  * `Мои сообщества` - Выводит список пользовательских сообществ
  * `Добавить сообщество(а)` - Добавляет сообщества в виде url ссылок из текста следующего сообщения пользователя
  * `Удалить сообщество(а)` - Удаляет сообщества в виде url ссылок или номеров сообществ из текста следующего сообщения пользователя
* `Добавить задачу` - Добавляет введённую задачу/заметку и закрепляет её за данным пользователем
* `Изменить задачу` - Изменяет введённую задачу/заметку, принадлежащую данному пользователю

**Примечание:** Также доступен голосовой ввод этих команд на русском языке.

## Зависимости
* [Python 3.7-3.8](https://www.python.org/downloads/)
* [ffmpeg](https://ffmpeg.org/download.html)
  * [Установка под Windows (на английском)](https://www.wikihow.com/Install-FFmpeg-on-Windows)
  * Установка под Ubuntu - выполнить команду `sudo apt install ffmpeg`
____________
> Библиотеки для Python: 
* [vk_api](https://github.com/python273/vk_api) - библиотека для работы бота с ВК
* [xlrd](https://github.com/python-excel/xlrd) - библиотека для парсинга .xlsx-файлов
* [Sphinx](https://github.com/sphinx-doc/sphinx) - библиотека для генерации документации
* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/) - библиотека для парсинга html страниц
* [PyMySQL](https://github.com/PyMySQL/PyMySQL) - библиотека, содержащая клиент для базы MySQL
* [cryptography](https://github.com/pyca/cryptography) - библиотека, для шифрования пароля при установлении соединения с базой данных
* [peewee](https://github.com/coleifer/peewee) - библиотека для работы с базой данных через удобные классы (ORM)
* [pyinstaller](https://github.com/pyinstaller/pyinstaller) - библиотека для сборки проекта в исполняемый файл
* [SpeechRecognition](https://github.com/Uberi/speech_recognition) - библиотека распознавания голосовых сообщений

## Установка зависимостей
Надо выполнить команду ниже в командной строке или терминале, находясь в корневой папке проекта.
```
pip install -r requirements.txt
```
**Примечание:** Вы должны иметь [requirements.txt](requirements.txt) в корневой папке проекта.

## Сборка

### Сборка приложения
Надо выполнить команду `make` в командной строке или терминале, находясь в корневой папке проекта.
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
Или исполнить основной файл `VkBotDiary.py` через команду `python VkBotDiary.py` или если в Linux `python3 VkBotDiary.py`,
предварительно установив все зависимости.

## Протестированные платформы
* Windows 7 или выше (32/64 бит)
* Linux (Ubuntu/Debian/CentOS)