from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Athlete, Event, Result, ApiKey
from .forms import ImportExcelForm
from .long_jump import export_long_jump_protocol
import openpyxl

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
    
    # Получаем ID соревнования (из GET запроса при выборе, или из POST при сохранении)
    active_event_id = request.POST.get('event') or request.POST.get('event_id') or event_id

    if active_event_id:
        current_event = Event.objects.filter(id=active_event_id).first()
        if current_event:
            athletes = Athlete.objects.filter(competition=current_event.competition).order_by('full_name')

    if request.method == "POST":
        athlete_id = request.POST.get('athlete_id')
        
        attempts = []
        for i in range(1, 7):
            val = request.POST.get(f'attempt_{i}')
            if val and val.strip() != '':
                try:
                    attempts.append(float(val.replace(',', '.')))
                except ValueError:
                    pass
        
        best_result = max(attempts) if attempts else None
        
        # Сохраняем результаты
        result_obj, created = Result.objects.update_or_create(
            event_id=active_event_id,
            athlete_id=athlete_id,
            defaults={
                'attempt_1': request.POST.get('attempt_1') or None,
                'attempt_2': request.POST.get('attempt_2') or None,
                'attempt_3': request.POST.get('attempt_3') or None,
                'attempt_4': request.POST.get('attempt_4') or None,
                'attempt_5': request.POST.get('attempt_5') or None,
                'attempt_6': request.POST.get('attempt_6') or None,
                'final_result': best_result
            }
        )
        
        # Безопасное сохранение ветра (если поля wind_1...wind_6 есть в модели Result)
        try:
            for i in range(1, 7):
                w_val = request.POST.get(f'wind_{i}')
                if w_val:
                    setattr(result_obj, f'wind_{i}', float(w_val.replace(',', '.')))
                else:
                    setattr(result_obj, f'wind_{i}', None)
            result_obj.save()
        except Exception:
            pass # Если полей в БД нет, просто пропускаем этот шаг

        messages.success(request, 'Результат сохранен!')
        return redirect(f'/judge/?event={active_event_id}&athlete_id={athlete_id}')

    selected_athlete_id = request.GET.get('athlete_id')
    existing_result = None
    
    if active_event_id and selected_athlete_id:
        existing_result = Result.objects.filter(
            event_id=active_event_id, 
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
    # Берем все результаты для этого соревнования
    results = Result.objects.filter(event_id=event_id).select_related("athlete")
    
    athletes_data = []
    for r in results:
        # Извлекаем ветер, если поля есть в БД, иначе ставим None
        winds = []
        for i in range(1, 7):
            winds.append(getattr(r, f'wind_{i}', None))

        athletes_data.append({
            "num": getattr(r.athlete, 'number', r.athlete.id), # Если есть поле "number", используется оно
            "order": r.id,
            "name": str(r.athlete), 
            "birth": getattr(r.athlete, 'birth_date', ''),
            "rank": getattr(r.athlete, 'rank', ''),
            "region": getattr(r.athlete, 'region', ''),
            "org": getattr(r.athlete, 'organization', ''),
            "attempts": [r.attempt_1, r.attempt_2, r.attempt_3, r.attempt_4, r.attempt_5, r.attempt_6],
            "winds": winds, 
            "result": r.final_result, 
            "coaches": getattr(r.athlete, 'coaches', ''),
        })

    event_info = {
        "title": "Открытый чемпионат и первенства города Абакана по лёгкой атлетике",
        "venue": "Легкоатлетический манеж МАУ 'СК им. Н.Г. Булакина', ул. Катанова, д. 10, стр. 1",
        "date": "07-08.2026",
        "time": "10:00",
        "stage": "финальные соревнования",
        "gender": "МУЖЧИНЫ",
        "discipline": "Прыжок в длину",
        "rm": ("7.37", "Хайке Дрехслер"),
        "re": ("7.37", "Хайке Дрехслер"),
        "rr": ("7.30", "Галина Чистякова"),
    }

    wb = export_long_jump_protocol(athletes_data, event_info)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="protocol_dlina.xlsx"'
    wb.save(response)
    return response
