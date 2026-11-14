from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Athlete, Event, Result, ApiKey
from .forms import ImportExcelForm

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
        current_event = Event.objects.get(id=event_id)
        athletes = Athlete.objects.filter(competition=current_event.competition).order_by('full_name')

    if request.method == "POST":
        event_id = request.POST.get('event_id')
        athlete_id = request.POST.get('athlete_id')
        
        attempts = []
        for i in range(1, 7):
            val = request.POST.get(f'attempt_{i}')
            if val:
                attempts.append(val)
        
        best_result = max(attempts) if attempts else ""

        Result.objects.update_or_create(
            event_id=event_id,
            athlete_id=athlete_id,
            defaults={
                'attempt_1': request.POST.get('attempt_1', ''),
                'attempt_2': request.POST.get('attempt_2', ''),
                'attempt_3': request.POST.get('attempt_3', ''),
                'attempt_4': request.POST.get('attempt_4', ''),
                'attempt_5': request.POST.get('attempt_5', ''),
                'attempt_6': request.POST.get('attempt_6', ''),
                'final_result': best_result
            }
        )
        messages.success(request, "Результат сохранен!")
        return redirect(f'/judge/?event={event_id}')

    return render(request, 'judge.html', {
        'events': events,
        'athletes': athletes,
        'current_event': current_event,
    })

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
import openpyxl
from django.http import HttpResponse

def export_excel(request, event_id):
    event = Event.objects.get(id=event_id)
    results = Result.objects.filter(event=event).order_by('-final_result') # Сортируем по убыванию (для прыжков)
    
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
from django.http import HttpResponse
from .long_jump import export_long_jump_protocol
from .models import Result

def export_long_jump(request, event_id):
    results = Result.objects.filter(event_id=event_id, discipline="длина").select_related("athlete")
    
    athletes_data = []
    for r in results:
        athletes_data.append({
            "num": r.athlete.number,
            "order": r.order,
            "name": r.athlete.full_name,
            "birth": r.athlete.birth_date,
            "rank": r.athlete.rank,
            "region": r.athlete.region,
            "org": r.athlete.organization,
            "attempts": [r.a1, r.a2, r.a3, r.a4, r.a5, r.a6],
            "winds": [r.w1, r.w2, r.w3, r.w4, r.w5, r.w6], # Ветер
            "result": r.best_result,
            "coaches": r.athlete.coaches,
        })

    event_info = {
        "title": "Открытый чемпионат и первенства города Абакана по лёгкой атлетике",
        "venue": "Легкоатлетический манеж МАУ 'СК им. Н.Г. Булакина', ул. Катанова, д. 10",
        "date": "07-08.2026",
        "time": "10:00",
        "stage": "финальные соревнования",
        "gender": "МУЖЧИНЫ",
        "discipline": "Прыжок в длину",
    }

    wb = export_long_jump_protocol(athletes_data, event_info)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="protocol_dlina.xlsx"'
    wb.save(response)
    return response
