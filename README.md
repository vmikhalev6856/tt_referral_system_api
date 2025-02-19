# api реферальной системы для controlgps.org (тестовое задание)

## описание

реализация регистрации и аутентификации пользователей (oauth2 bearer jwt), а так же простой реферальной системы (регистрация по реферальному коду, управление реферальным кодом и просмотр рефералов) в рамках тестового задания для controlgps.org

![скриншот документации swagger](image.png)

## требования для выполнения команд по установке и запуску

- macos/linux/wsl
- docker
- docker-compose

## установка и запуск

1. **клонируем репозиторий**

   ```sh
   git clone https://github.com/vmikhalev6856/tt_referral_system_api.git &&
   cd tt_referral_system_api
   ```

2. **создаём `.env` файл на базе `.env.example`**

   ```sh
   cp .env.example .env
   ```

   _отредактируйте `.env`: нужно заменить только значение переменной `EMAIL_HUNTER_API_KEY` (значение этого ключа я передал в переписке), он нужен для верификации email сторонним сервисом при регистрации новых пользователей (остальное можно оставить как есть, все будет работать)_

3. **запускаем контейнеры c миграциями для инициализации базы данны проекта**

   _в последнее время есть периодические небольшие сложности с подключением к docker regetry для получения разной служебной метаинформации, и из-за этого билд контейров может прерваться с ошибкой. в этом случае - просто выполните команду со сборкой и запуском заново_

   ```sh
   docker-compose up -d &&
   docker-compose exec tt_referral_system_api poetry run alembic upgrade head
   ```

4. **проверяем, что api работает**

   swagger доступен по адресу [http://localhost:8000/docs](http://localhost:8000/docs)

   альтернативная документация (redoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

## тестирование api через swagger

1. **открываем swagger** [http://localhost:8000/docs](http://localhost:8000/docs)

2. **регистрируем нового пользователя**

   - находим `POST /user/registration`
   - нажимаем `try it out`
   - заполняем `email`, `password` и (опционально, `null` без ковычек там) `referral_code`
   - нажимаем `execute`
   - получаем объект с зарегистрированным пользователем

   сервис использует стороннее апи для верификации email, поэтому число регистраций ограничено и пройдет регистрация только с email, на который, в теории, можно отправить письмо. указать для тестов можно любые (главное, что настоящие)

3. **логинимся**

   - находим `POST /user/login`
   - вводим `email` и `password`
   - нажимаем `execute`
   - копируем `access_token` из ответа

4. **тестируем защищенные ручки**

   - нажимаем `authorize` в верхнем правом углу
   - вводим скопированный `access_token` с `bearer jwt`
   - теперь можно отправлять запросы к защищенным эндпоинтам

5. **создаём реферальный код:**

   - переходим в `POST /referral_code/create`
   - указываем `lifetime_in_hours` в часах (больше единицы)
   - нажимаем `execute`
   - получаем реферальный код

6. **удаляем реферальный код:**

   - переходим в `DELETE /referral_code/delete`
   - нажимаем `execute`
   - код удалён

_думаю, логика работы с апи понятна. рекомендую открыть сразу несколько вкладок, чтобы не мучаться с токенами для аутентификации каждого пользователя для тестов_

## структура проекта

```sh
.
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── alembic # миграции
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 7b7f97aa8fc5_.py
├── alembic.ini
├── app # папка проекта
│   ├── __init__.py
│   ├── api # роутинг
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── referral_code.py
│   │       └── user.py
│   ├── core # ядро проекта с настройками всего
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── security.py
│   │   └── utils.py
│   ├── crud # операции с базой данных
│   │   ├── __init__.py
│   │   ├── referral_code.py
│   │   └── user.py
│   ├── dependences.py # внутренние зависимости
│   ├── main.py # инициализация приложения
│   └── models # модельки для базы данных и запросов с ответами
│       ├── __init__.py
│       ├── jwt.py
│       ├── referral_code.py
│       └── user.py
├── docker-compose.yml
├── poetry.lock
└── pyproject.toml
```

## итог

теперь api полностью настроен и готов к ручному тестированию. весь код задокументирован и в самой документации api все подробно описано

_из фишечек проекта проекта могу отметить использование hash индексов в postgres для таблицы с пользователями (даже на id так-как стандартный b-tree индекс не работает быстро на uuid идентификаторах, а в проекте именно они), а также реализацию отзыва jwt для аутентификации и обновления пары токенов (кстати, реализована проверка браузера или клиента для проверки использования токена на том клиенте, где выдавался. мелочь и легко обходится, но лишает возможности просто взять и воспользоваться токенами на другом клиенте без добавления соответсвующего заголовка)_

_из минусов – отсутствие автотестов для бд и ручек_
