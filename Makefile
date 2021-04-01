ifeq ($(OS),Windows_NT)
    uname_S := Windows
else
    uname_S := $(shell uname -s)
endif

ifeq ($(uname_S), Windows)
    target = VkBot_Diary.exe
    _clean = clear_win
endif
ifeq ($(uname_S), Linux)
    target = VkBot_Diary
    _clean = clear_lin
endif

.PHONY = clean_lin, clear_win

install: $(target) $(_clean)

$(target):
	pyinstaller -F --icon=bot.ico --distpath=./build_dist VkBotDiary.py
	@echo Собрано

clear_lin:
	$(shell rm -f -r ./build)
	$(shell rm -f *.spec)
	@echo Очищено

clear_win:
	cmd /c "rd /s /q build"
	del *.spec
	@echo Очищено