#!/bin/bash

# 1. Обновляем базу данных (создаем новые колонки is_running и time_result)
python manage.py makemigrations core
python manage.py migrate

# 2. Собираем статику (чтобы админка выглядела красиво)
python manage.py collectstatic --noinput

# 3. Создаем администратора (если его нет)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username='admin')
user.set_password('Abakan2026!')
user.is_superuser = True
user.is_staff = True
user.save()
"

# 4. Заполняем базу начальными данными (Соревнование, Виды спорта)
python manage.py shell -c "
from core.models import Competition, Event, Athlete
try:
    comp = Competition.objects.get(name='Открытие 2026')
    
    Athlete.objects.filter(competition__isnull=True).update(competition=comp)

    technical_events = [
        ('Прыжок в длину', 'М', '2008 и ст.'), ('Прыжок в длину', 'М', '2009-2010'), ('Прыжок в длину', 'М', '2011-2012'),
        ('Прыжок в длину', 'Ж', '2008 и ст.'), ('Прыжок в длину', 'Ж', '2009-2010'), ('Прыжок в длину', 'Ж', '2011-2012'),
        ('Толкание ядра', 'М', '2008 и ст.'), ('Прыжок с шестом', 'М', '2008 и ст.'), ('Прыжок в высоту', 'М', '2008 и ст.'), ('Тройной прыжок', 'М', '2008 и ст.'),
        ('Толкание ядра', 'Ж', '2008 и ст.'), ('Тройной прыжок', 'Ж', '2008 и ст.'), ('Прыжок с шестом', 'Ж', '2008 и ст.'), ('Прыжок в высоту', 'Ж', '2008 и ст.'),
        ('Тройной прыжок', 'М', '2009-2010'), ('Прыжок в высоту', 'М', '2009-2010'), ('Толкание ядра', 'М', '2009-2010'), ('Прыжок с шестом', 'М', '2009-2010'),
        ('Тройной прыжок', 'М', '2011-2012'), ('Прыжок в высоту', 'М', '2011-2012'), ('Толкание ядра', 'М', '2011-2012'), ('Прыжок с шестом', 'М', '2011-2012'),
        ('Тройной прыжок', 'Ж', '2009-2010'), ('Прыжок в высоту', 'Ж', '2009-2010'), ('Толкание ядра', 'Ж', '2009-2010'), ('Прыжок с шестом', 'Ж', '2009-2010'),
        ('Тройной прыжок', 'Ж', '2011-2012'), ('Прыжок в высоту', 'Ж', '2011-2012'), ('Толкание ядра', 'Ж', '2011-2012'), ('Прыжок с шестом', 'Ж', '2011-2012'),
    ]
    
    for name, gender, category in technical_events:
        Event.objects.get_or_create(competition=comp, name=name, gender=gender, category=category, is_technical=True, is_running=False)

    running_events = [
        ('Бег 100 м', 'М', '2008 и ст.'), ('Бег 100 м', 'Ж', '2008 и ст.'),
        ('Бег 200 м', 'М', '2008 и ст.'), ('Бег 200 м', 'Ж', '2008 и ст.'),
        ('Бег 400 м', 'М', '2008 и ст.'), ('Бег 400 м', 'Ж', '2008 и ст.'),
        ('Бег 800 м', 'М', '2008 и ст.'), ('Бег 800 м', 'Ж', '2008 и ст.'),
    ]
    
    for name, gender, category in running_events:
        Event.objects.get_or_create(competition=comp, name=name, gender=gender, category=category, is_technical=False, is_running=True)

    print('Данные обновлены!')
except Competition.DoesNotExist:
    print('Соревнование не найдено')
"

# 5. Запускаем сам сайт
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
