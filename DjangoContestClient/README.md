# DjangoContestClient

Минимальное Django-приложение, повторяющее основной сценарий `PythonContestClient`:

- загрузка пользователя
- выбор курса и языка
- получение набора задач из `ContestServer`
- выбор задачи и варианта
- загрузка файла с решением
- отправка на проверку и показ результата
- сброс сессии

Дополнительно есть staff-only раздел `/ops/` для администрирования `ContestServer`:

- просмотр курсов
- просмотр пользователей
- просмотр задач курса
- очистка курса
- получение дампа сообщений
- CRUD-операции по задачам
- пакетный импорт задач из JSON

## Запуск

```bash
cd DjangoContestClient
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

После запуска открой:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/admin/`

После входа staff-пользователем будет доступен административный раздел:

- `http://127.0.0.1:8000/ops/`

## Запуск через Docker Compose

Из корня репозитория:

```bash
docker compose up --build django-client
```

Сервис поднимет Django, выполнит `migrate`, создаст superuser при первом старте и запустит приложение на:

- `http://127.0.0.1:8000/`

Для Docker Compose заранее настроен superuser:

- username: `sinegordon`

Переменные superuser читаются из корневого `.env`.
