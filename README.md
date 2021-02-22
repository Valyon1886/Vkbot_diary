# Vkbot_diary

## Установка mysql server 8.0 (Самый свежий... потому, что почему бы и нет?) 👌 )

> В терминале выполняем следующие команды:
- `sudo apt-get update && sudo apt-get upgrade`
- `sudo apt-get install mysql-server`
- Запускаем скрипт первичной настройки БД `sudo mysql_secure_installation`
  - Там надо будет указать сложность пароля и сам пароль ***для пользователя root!***
  - `Remove anonymous users?` - удаление анонимных пользователей - что хотите, всё равно своего пользователя будем создавать
  - `Disallow root login remotely?` - запрет на подключение через пользователь root удалённо - то же самое
  - `Remove test database and access to it?` - удаление тестовой базы данных - да (Y)
  - `Reload privilege tables now?` - перезагрузить превелегии - да (Y)

## Настройка mysql

> В файле /etc/mysql/mysql.conf.d/mysqld.cnf
* Меняем ip адрес у bind-address с 127.0.0.1 на 0.0.0.0
```yaml
[mysqld]
#
# * Basic Settings
#
user            = mysql
# pid-file      = /var/run/mysqld/mysqld.pid
# socket        = /var/run/mysqld/mysqld.sock
# port          = 3306
# datadir       = /var/lib/mysql


# If MySQL is running as a replication slave, this should be
# changed. Ref https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_tmpdir
# tmpdir                = /tmp
#
# Instead of skip-networking the default is now to listen only on
# localhost which is more compatible and is not less secure.
bind-address            = 127.0.0.1 # <- Вот он!
mysqlx-bind-address     = 127.0.0.1
```
> Далее в терминале выполняем
* `systemctl enable mysql`
* `systemctl restart mysql`
* После можете ещё проверить статус службы БД `systemctl status mysql` если хотите 🧐, должно быть так
```
root@ubuntu:/home/user01# systemctl status mysql
● mysql.service - MySQL Community Server
     Loaded: loaded (/lib/systemd/system/mysql.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2021-02-22 08:48:27 PST; 2min 16s ago
    Process: 4092 ExecStartPre=/usr/share/mysql/mysql-systemd-start pre (code=exited, status=0/SUCCESS)
   Main PID: 4100 (mysqld)
     Status: "Server is operational"
      Tasks: 38 (limit: 3487)
     Memory: 338.0M
     CGroup: /system.slice/mysql.service
             └─4100 /usr/sbin/mysqld

Feb 22 08:48:26 ubuntu systemd[1]: Starting MySQL Community Server...
Feb 22 08:48:27 ubuntu systemd[1]: Started MySQL Community Server.
```
> Чтобы подключиться к терминалу mysql с линуксовой машины печатаем в терминале `mysql -u root -p`, enter и на следующей строке вводим пароль для root, который вы указали в скрипте!
<!-- -->
> В терминале mysql
* Cоздаём юзверя 'user' с паролем 'password' (% обозначает, что через этого пользователя можно подключаться с любого устройства): `create user 'user'@'%' identified by 'password';`
* Добавляем ему разрешения на всё: `GRANT ALL PRIVILEGES ON *.* TO 'user'@'%';`
* Перезагружаем привелегии: `FLUSH PRIVILEGES;`
> Там, где вы подключаетесь указывайте ip вашей виртуалки и порт (по умолчанию 3306), а также логин и пароль нужного юзверя (похожего на верхнего).
<!-- -->
> Проверяем, что коннект есть - профит!
<!-- -->
> Далее работаем с БД на винде или где вы там работаете) Это пример запроса, который создаёт базу данных `test1` переключается на неё и создаёет в ней таблицу `tutorials_tbl` вида

<img src="https://i.ibb.co/37tDpkx/EXPL-DB.png"/>

```mysql
create database test1;
use test1;
create table tutorials_tbl(
   tutorial_id INT NOT NULL AUTO_INCREMENT,
   tutorial_title VARCHAR(100) NOT NULL,
   tutorial_author VARCHAR(40) NOT NULL,
   submission_date DATE,
   PRIMARY KEY ( tutorial_id )
);
```
