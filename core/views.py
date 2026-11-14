from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Athlete, Event, Result, ApiKey
from .forms import ImportExcelForm
import openpyxl
from django.http import HttpResponse
# ИСПРАВЛЕНО: Импортируем правильное название функции
from .long_jump import export_technical_protocol 


def home(request):
    return render(request, 'home.html')


def upload_excel(request):
    if request.method == "POST":
        form = ImportExcelForm(request.POST, request.FILES)
        if form.is_valid():
            count = form.save()
            messages.success(request, f"Успешно загружено {count} участников!")
            return redirect('admin:core_athlete_changelist')
    else:
        form = ImportExcelForm()
    return render(request, 'upload_excel.html', {'form': form})


def judge_input(request):
    events = Event.objects.filter(is_technical=True)
    event_id = request.GET.get('event')
    athletes = []
    current_event = None
    
    if event_id:
        current_event = Event.objects.filter(id=event_id).first()
        if current_event:
            athletes = Athlete.objects.filter(competition=current_event.competition).order_by('full_name')

    if request.method == "POST":
        event_id = request.POST.get('event_id') or request.POST.get('event')
        athlete_id = request.POST.get('athlete_id')
        
        # Вспомогательная функция для безопасного перевода текста в число
        def parse_float(val):
            if not val or str(val).strip() == '': 
                return 0.0
            val = str(val).strip().upper()
            # Если судья ввел X или прочерк - это неудачная попытка (-1.0)
            if val in ['X', 'Х', '-', 'МИМО', 'НЕУДАЧА']: 
                return -1.0
            try:
                return float(val.replace(',', '.'))
            except ValueError:
                return 0.0

        # Сохраняем попытки и ветер
        attempts = [parse_float(request.POST.get(f'attempt_{i}')) for i in range(1, 7)]
        winds = [parse_float(request.POST.get(f'wind_{i}')) for i in range(1, 7)]
        
        # Считаем лучший результат (игнорируем неудачные попытки -1.0 и нули)
        valid_attempts = [a for a in attempts if a > 0]
        best_result = max(valid_attempts) if valid_attempts else 0.0
        
        # Галочка рекорда
        is_record = request.POST.get('is_record') == 'on'
        
        Result.objects.update_or_create(
            event_id=event_id,
            athlete_id=athlete_id,
            defaults={
                'attempt_1': attempts[0], 'attempt_2': attempts[1], 'attempt_3': attempts[2],
                'attempt_4': attempts[3], 'attempt_5': attempts[4], 'attempt_6': attempts[5],
                'wind_1': winds[0], 'wind_2': winds[1], 'wind_3': winds[2],
                'wind_4': winds[3], 'wind_5': winds[4], 'wind_6': winds[5],
                'final_result': best_result,
                'is_record': is_record
            }
        )
        messages.success(request, 'Результат сохранен!')
        return redirect(f'/judge/?event={event_id}&athlete_id={athlete_id}')

    selected_athlete_id = request.GET.get('athlete_id')
    existing_result = None
    
    if event_id and selected_athlete_id:
        existing_result = Result.objects.filter(
            event_id=event_id, 
            athlete_id=selected_athlete_id
        ).first()

    context = {
        'events': events,
        'athletes': athletes,
        'current_event': current_event,
        'selected_athlete_id': int(selected_athlete_id) if selected_athlete_id else None,
        'existing_result': existing_result, 
    }
    return render(request, 'judge.html', context)


@csrf_exempt
def input_result(request):
    if request.method == "POST":
        key = request.headers.get("X-Api-Key")
        try:
            api_key = ApiKey.objects.get(key=key, is_active=True)
        except ApiKey.DoesNotExist:
            return JsonResponse({"error": "Неверный ключ"}, status=403)

        athlete_id = request.POST.get("athlete_id")
        value = request.POST.get("value")
        
        event = api_key.event
        if not event:
            return JsonResponse({"error": "Ключ не привязан к виду"}, status=400)

        result, _ = Result.objects.update_or_create(
            event=event,
            athlete_id=athlete_id,
            defaults={"final_result": value}
        )
        return JsonResponse({"status": "ok", "id": result.id})
    
    return JsonResponse({"error": "Метод не разрешен"}, status=405)


def export_excel(request, event_id):
    event = Event.objects.get(id=event_id)
    results = Result.objects.filter(event=event).order_by('-final_result')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = event.name
    
    ws.append(["Место", "ФИО", "Год рождения", "Организация", "Попытка 1", "Попытка 2", "Попытка 3", "Попытка 4", "Попытка 5", "Попытка 6", "Лучший результат"])
    
    for index, res in enumerate(results, start=1):
        ws.append([
            index,
            res.athlete.full_name,
            res.athlete.birth_date.year if res.athlete.birth_date else "",
            res.athlete.organization,
            res.attempt_1 or "",
            res.attempt_2 or "",
            res.attempt_3 or "",
            res.attempt_4 or "",
            res.attempt_5 or "",
            res.attempt_6 or "",
            res.final_result or ""
        ])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{event.name}.xlsx"'
    wb.save(response)
    return response


def export_long_jump(request, event_id):
    discipline = request.GET.get('discipline', 'длина').lower()
    gender_param = request.GET.get('gender', 'м').lower()
    
    discipline_titles = {
        'длина': 'Прыжок в длину',
        'высота': 'Прыжок в высоту',
        'тройной': 'Тройной прыжок',
        'ядро': 'Толкание ядра'
    }
    title = discipline_titles.get(discipline, 'Технический вид')
    gender_title = "ЖЕНЩИНЫ" if gender_param == 'ж' else "МУЖЧИНЫ"

    results = Result.objects.filter(event_id=event_id).select_related("athlete")
    
    athletes_data = []
    for r in results:
        athletes_data.append({
            "num": r.id, 
            "order": r.id,
            "name": str(r.athlete), 
            "birth": getattr(r.athlete, 'birth_date', ''),
            "rank": getattr(r.athlete, 'rank', ''),
            "region": getattr(r.athlete, 'region', ''),
            "org": getattr(r.athlete, 'organization', ''),
            "attempts": [r.attempt_1, r.attempt_2, r.attempt_3, r.attempt_4, r.attempt_5, r.attempt_6],
            "winds": [
                getattr(r, 'wind_1', None), getattr(r, 'wind_2', None), getattr(r, 'wind_3', None),
                getattr(r, 'wind_4', None), getattr(r, 'wind_5', None), getattr(r, 'wind_6', None)
            ], 
            "result": r.final_result, 
            "coaches": getattr(r.athlete, 'coach', ''), 
        })

    event_info = {
        "title": "Открытый чемпионат и первенства города Абакана по лёгкой атлетике",
        "venue": "Легкоатлетический манеж МАУ 'СК им. Н.Г. Булакина', ул. Катанова, д. 10, стр. 1",
        "date": "07-08.2026",
        "time": "10:00",
        "stage": "финальные соревнования",
        "gender": gender_title,
        "discipline": title,
        "rm": ("", ""), 
        "re": ("", ""),
        "rr": ("", ""),
    }

    # ИСПРАВЛЕНО: Вызываем export_technical_protocol
    wb = export_technical_protocol(athletes_data, event_info) 

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="protocol_{discipline}_{gender_param}.xlsx"'
    wb.save(response)
    return response
