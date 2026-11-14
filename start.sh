#!/bin/bash
python manage.py makemigrations core
python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username='admin')
user.set_password('Abakan2026!')
user.is_superuser = True
user.is_staff = True
user.save()
"

gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
