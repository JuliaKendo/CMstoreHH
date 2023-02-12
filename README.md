# Бот информирующий в телеграмме о изменении статусов резюме на Head Hanter

Бот информирующий в телеграмме о изменении статусов резюме на Head Hanter.

# Содержание

- [Установка](#установка)
  - [Переменные окружения](#установите-переменные-окружения)
  - [Подключение google таблицы](#подключите-google-таблицу)
- [Процедура запуска](#процедура-запуска)
- [Использование бота](#использование-бота)


# Установка

Клонируйте репозиторий, и создайте виртуальное окружение. После этого установите зависимости:

```
$ python3 -m venv env
$ . env/bin/activate
(env) $ pip install -r requirements.txt
```

При деплое на облачное хранилище используйте docker compose:

```
$ docker-compose up
```


## Установите переменные окружения

`HH_CLIENT_SECRET` - Секретный ключ полученный при регистрации приложения на hh.ru.

`HH_CLIENT_ID` - ID приложения на hh.ru.

`HH_EMAIL` - Email пользователя hh.ru.

`HH_PASSWORD` - Пароль пользователя hh.ru.

`SELENIUM_SERVER` - Адрес сервера селениум в формате <ip>:<port>. При деплое с использованием docker compose в качетстве адреса указываем hostname и port из файла docker-compose.yml.

`REDIS_SERVER` - Адрес сервера redis в формате <ip>:<port>. При деплое с использованием docker compose в качетстве адреса указываем hostname и port из файла docker-compose.yml.

`GOOGLE_SPREADSHEET_ID` - ID googl таблицы со списком отслеживаемых имен сотрудников. Его можно извлечь из адресной строки таблицы в браузере `https://docs.google.com/spreadsheets/d/ <ID> /...`.

`GOOGLE_RANGE_NAME` - Имя листа и область таблицы со списком отслеживаемых имен сотрудников, в формате Лист1!A1:A999.

`ROLLBAR_TOKEN` - Токен службы мониторинга rollbar.


## Подключите google таблицу

Для получения списка пользователей бот использует google таблицу. Таблица должна быть создана в следующем формате:
  - Первая колонка (А): Фамилия Имя Отчество сотрудников
  - Вторая колонка (В): ID резюме сотрудника на Head Hanter.
ID можно извлечь из адресной строки резюме в браузере `https://www.hh.ru/resume/ <ID> ?...`.

Для подключения google таблицы к проекту необходимо файл credentials.json положить в корень проекта. Алгоритм получения этого файла описан в документации [google api](https://developers.google.com/sheets/api/quickstart/python).

# Процедура запуска

```bash
$ python main.py
```

Для запуска бота в виде сервиса поместить файл `CMstoreHH.service` в `/etc/systemd/system`, затем вести следующую комманду:

```bash
$ systemctl start CMstoreHH
```


# Использование бота

При первом запуске выберите комманду или введите /start. Появиться клавиатура. Для начала отслеживания необходимо нажать `Запустить`. В случае необходимости прекратить отслеживание, выбираем `Остановить`. Что бы перезапустить бота нажимаем или вводим комманду /start.