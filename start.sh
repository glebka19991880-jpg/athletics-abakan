#!/bin/bash

# Жестко указываем базу данных
export DATABASE_URL=${{Postgres.DATABASE_URL}}

# Применяем миграции
python manage.py migrate

# Создаем админа
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'Abakan2026!')
"

# Запускаем сервер
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
