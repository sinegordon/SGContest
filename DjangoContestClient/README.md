# DjangoContestClient

Минимальное Django-приложение, повторяющее основной сценарий `PythonContestClient`:

- загрузка пользователя
- выбор курса и языка
- получение набора задач из `ContestServer`
- выбор задачи и варианта
- загрузка файла с решением
- отправка на проверку и показ результата
- сброс сессии

## Запуск

```bash
cd DjangoContestClient
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

После запуска открой:

- `http://127.0.0.1:8000/`
