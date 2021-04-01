@ECHO OFF
chcp 65001
:build
pyinstaller -F --icon=bot.ico --distpath=./build_dist --name=VkBot_Diary.exe VkBotDiary.py
echo Собрано
:clear
rd /s /q build
del *.spec
echo Очищено