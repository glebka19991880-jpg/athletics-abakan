#!/bin/bash
python manage.py makemigrations core
python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'abakan2026!')
"

gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
