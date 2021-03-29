@ECHO off
chcp 65001
cls
:start
echo 1. Сгенерить apidoc
echo 2. Не генерить apidoc
set choice=
set /p choice="Введите цифру - "
if '%choice%'=='' set choice=%choice:1%
if '%choice%'=='1' goto apidoc
if '%choice%'=='2' goto docs
ECHO "%choice%" is not valid, try again
:apidoc
sphinx-apidoc ../ -o ./source -f
:docs
echo Если не знаете цель для make введите help
set choice2=
set /p choice2="Введите цель для make - "
if not '%choice2%'=='' set choice=%choice:help%
if '%choice2%'=='1' goto make
if '%choice2%'=='2' goto help
:make
make %choice2%
goto end
:help
start /wait make
@pause
goto docs
:end