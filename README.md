# api реферальной системы для controlgps.org (тестовое задание)

## описание

реализация управления реферальными кодами и регистрации пользователей (oauth2 bearer jwt) в рамках тестового задания для controlgps.org

## требования

- docker и docker compose

## установка и запуск

1. **клонируем репозиторий:**

   ```sh
   git clone https://github.com/vmikhalev6856/tt_referral_system_api.git;
   cd tt_referral_system_api
   ```

2. **создаём .env файл:**

   ```sh
   cp .env.example .env
   ```

   отредактируй `.env`, нужно заменить только `EMAIL_HUNTER_API_KEY`, который я передал в переписке, он нужен для проверки почтовый ящиков сторонним сервисом при регистрации (остальное можно оставить как есть, все будет работать)

3. **запускаем контейнеры:**

   ```sh
   docker-compose up
   ```

4. **применяем миграции:**

    в новой оболочке терминала уже (в новом окне)

   ```sh
   docker-compose exec tt_referral_system_api poetry run alembic upgrade head
   ```

5. **проверяем, что api работает:**

   swagger доступен по адресу:

   [http://localhost:8000/docs](http://localhost:8000/docs)

   альтернативная документация redoc:

   [http://localhost:8000/redoc](http://localhost:8000/redoc)

## тестирование api через swagger

1. **открываем swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

2. **регистрируем нового пользователя:**

   - находим `POST /user/registration`
   - нажимаем `try it out`
   - заполняем `email`, `password` и (опционально, `null` без ковычек там) `referral_code`
   - нажимаем `execute`
   - получаем объект с зарегистрированным пользователем

   сервис использует стороннее апи для верификации email, поэтому число регистраций ограничено и пройдет регистрация только с email, на который, в теории, можно отправить письмо. указать для тестов можно любые (главное, что настоящие)

3. **логинимся:**

   - находим `POST /user/login`
   - вводим `email` и `password`
   - нажимаем `execute`
   - копируем `access_token` из ответа

4. **тестируем защищенные ручки:**

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

думаю, логика работы с апи понятна

## структура проекта

выглядеть перед билдом все должно так

```bash
.
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 7b7f97aa8fc5_.py
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── referral_code.py
│   │       └── user.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── security.py
│   │   └── utils.py
│   ├── crud
│   │   ├── __init__.py
│   │   ├── referral_code.py
│   │   └── user.py
│   ├── dependences.py
│   ├── main.py
│   └── models
│       ├── __init__.py
│       ├── jwt.py
│       ├── referral_code.py
│       └── user.py
├── docker-compose.yml
├── poetry.lock
└── pyproject.toml
```

## итог

теперь api полностью настроен и готов к тестированию.

при выполнении тестового задания я использовал асинхронный редис для кеша и асинхронную постгрес с хэш индексами вместо b-tree для моментального поиска.

так же я посторался максимально задокументировать на русском языке весь код и документацию апи для простоты восприятия.

на тестирование, к сожадению, не так много времени, к тому же - я бы многое улучшил и оптимизировал еще
