# SGContest

Репозиторий содержит несколько клиентов и серверную часть для системы проверки задач.

## Структура

- [ContestServer](./ContestServer/README) — backend c JSON-RPC API через `POST /api/run`
- [PythonContestClient](./PythonContestClient/client.py) — desktop-клиент на PyQt
- [DjangoContestClient](./DjangoContestClient/README.md) — минимальный web-клиент на Django
- [WebCSContestClient](./WebCSContestClient/README.md) — ASP.NET-клиент

## Django-приложение

[DjangoContestClient](./DjangoContestClient/README.md) повторяет основную функциональность `PythonContestClient` в веб-формате:

- загрузка пользователя
- выбор курса
- получение набора задач из `ContestServer`
- выбор задачи
- случайный выбор варианта задачи при первичной выдаче студенту
- загрузка файла с решением
- асинхронная отправка на проверку без перезагрузки страницы
- выбор языка проверки в момент отправки решения
- сброс сессии

Также в Django-клиенте есть staff-only раздел `/ops/` для администрирования сервиса:

- просмотр курсов
- просмотр пользователей
- просмотр задач курса
- создание курса
- создание пользователя
- очистка курса
- настройка количества задач каждого уровня отдельно для каждого курса
- загрузка данных курса для пересчёта реальных лимитов по уровням
- сброс назначенного набора задач у студента по курсу
- пакетный импорт задач из JSON
- получение дампа сообщений в виде JSON-файла

## Быстрый запуск DjangoContestClient

```bash
cd DjangoContestClient
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

После запуска:

- пользовательский интерфейс: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`
- ops-панель: `http://127.0.0.1:8000/ops/`

Для доступа к `/ops/` нужен staff-пользователь Django.

## Запуск через Docker Compose

В корневом `docker-compose.yml` есть отдельный сервис `django-client`.

После запуска:

```bash
docker compose up --build django-client
```

будут доступны:

- пользовательский интерфейс Django-клиента: `http://127.0.0.1:8000/`
- backend `ContestServer`: `http://127.0.0.1:57888/`
- Django admin: `http://127.0.0.1:8000/admin/`
- ops-панель: `http://127.0.0.1:8000/ops/`

При старте `django-client` автоматически создаётся Django superuser:

- username: `sinegordon`

Переменные суперпользователя теперь читаются из корневого `.env`.

Полезные команды:

```bash
docker compose up --build
docker compose down
```
