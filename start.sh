#!/bin/bash
python manage.py makemigrations core
python manage.py migrate

# Создаем админа
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username='admin')
user.set_password('Abakan2026!')
user.is_superuser = True
user.is_staff = True
user.save()
"

# Создаем виды спорта
python manage.py shell -c "
from core.models import Competition, Event
try:
    comp = Competition.objects.get(name='Открытие 2026')
    events_data = [
        ('Прыжок в длину', 'М', '2008 и ст.'),
        ('Прыжок в длину', 'М', '2009-2010'),
        ('Прыжок в длину', 'М', '2011-2012'),
        ('Прыжок в длину', 'Ж', '2008 и ст.'),
        ('Прыжок в длину', 'Ж', '2009-2010'),
        ('Прыжок в длину', 'Ж', '2011-2012'),
        ('Толкание ядра', 'М', '2008 и ст.'),
        ('Прыжок с шестом', 'М', '2008 и ст.'),
        ('Прыжок в высоту', 'М', '2008 и ст.'),
        ('Тройной прыжок', 'М', '2008 и ст.'),
        ('Толкание ядра', 'Ж', '2008 и ст.'),
        ('Тройной прыжок', 'Ж', '2008 и ст.'),
        ('Прыжок с шестом', 'Ж', '2008 и ст.'),
        ('Прыжок в высоту', 'Ж', '2008 и ст.'),
        ('Тройной прыжок', 'М', '2009-2010'),
        ('Прыжок в высоту', 'М', '2009-2010'),
        ('Толкание ядра', 'М', '2009-2010'),
        ('Прыжок с шестом', 'М', '2009-2010'),
        ('Тройной прыжок', 'М', '2011-2012'),
        ('Прыжок в высоту', 'М', '2011-2012'),
        ('Толкание ядра', 'М', '2011-2012'),
        ('Прыжок с шестом', 'М', '2011-2012'),
        ('Тройной прыжок', 'Ж', '2009-2010'),
        ('Прыжок в высоту', 'Ж', '2009-2010'),
        ('Толкание ядра', 'Ж', '2009-2010'),
        ('Прыжок с шестом', 'Ж', '2009-2010'),
        ('Тройной прыжок', 'Ж', '2011-2012'),
        ('Прыжок в высоту', 'Ж', '2011-2012'),
        ('Толкание ядра', 'Ж', '2011-2012'),
        ('Прыжок с шестом', 'Ж', '2011-2012'),
    ]
    for name, gender, category in events_data:
        Event.objects.get_or_create(competition=comp, name=name, gender=gender, category=category, is_technical=True)
    print('Виды успешно созданы!')
except Competition.DoesNotExist:
    print('Соревнование Открытие 2026 не найдено')
"

gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
