from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Athlete, Event, Result, ApiKey
from .forms import ImportExcelForm
import openpyxl
from django.http import HttpResponse
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
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Доступ запрещен. В ссылке отсутствует параметр ?token=...", status=403)
    
    try:
        api_key = ApiKey.objects.get(key=token, is_active=True)
    except ApiKey.DoesNotExist:
        return HttpResponse("Доступ запрещен. Неверный или неактивный API-ключ.", status=403)

    current_event = api_key.event
    events = Event.objects.filter(id=current_event.id)
    athletes = Athlete.objects.filter(competition=current_event.competition).order_by('full_name')

    if request.method == "POST":
        event_id = request.POST.get('event_id') or request.POST.get('event')
        if str(current_event.id) != str(event_id):
            return HttpResponse("Ошибка: вы пытаетесь сохранить результат в чужое соревнование.", status=403)

        athlete_id = request.POST.get('athlete_id')
        
        def parse_float(val):
            if not val or str(val).strip() == '': 
                return 0.0
            val = str(val).strip().upper()
            if val in ['X', 'Х', '-', 'МИМО', 'НЕУДАЧА']: 
                return -1.0
            try:
                return float(val.replace(',', '.'))
            except ValueError:
                return 0.0

        attempts = [parse_float(request.POST.get(f'attempt_{i}')) for i in range(1, 7)]
        valid_attempts = [a for a in attempts if a > 0]
        best_result = max(valid_attempts) if valid_attempts else 0.0
        
        Result.objects.update_or_create(
            event_id=current_event.id,
            athlete_id=athlete_id,
            defaults={
                'attempt_1': attempts[0], 'attempt_2': attempts[1], 'attempt_3': attempts[2],
                'attempt_4': attempts[3], 'attempt_5': attempts[4], 'attempt_6': attempts[5],
                'final_result': best_result
            }
        )
        messages.success(request, 'Результат сохранен!')
        return redirect(f'/judge/?token={token}&event={current_event.id}&athlete_id={athlete_id}')

    selected_athlete_id = request.GET.get('athlete_id')
    existing_result = None
    
    if current_event and selected_athlete_id:
        existing_result = Result.objects.filter(
            event_id=current_event.id, 
            athlete_id=selected_athlete_id
        ).first()

    context = {
        'events': events,
        'athletes': athletes,
        'current_event': current_event,
        'selected_athlete_id': int(selected_athlete_id) if selected_athlete_id else None,
        'existing_result': existing_result, 
        'token': token,
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
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Доступ запрещен. Отсутствует API-ключ (token).", status=403)
    
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
            "winds": [None, None, None, None, None, None], 
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

    wb = export_technical_protocol(athletes_data, event_info) 

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="protocol_{discipline}_{gender_param}.xlsx"'
    wb.save(response)
    return response


# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ДЛЯ ЗРИТЕЛЕЙ ---
def spectator_results(request):
    events = Event.objects.all().order_by('name')
    
    selected_gender = request.GET.get('gender')
    selected_category = request.GET.get('category')
    
    if selected_gender:
        if selected_gender == 'М':
            events = events.filter(gender__icontains='м')
        elif selected_gender == 'Ж':
            events = events.filter(gender__icontains='ж')
            
    if selected_category:
        events = events.filter(category__icontains=selected_category)

    events_data = []
    for event in events:
        # Берем ВСЕХ спортсменов, которые заявлены в этом соревновании (competition)
        if not event.competition:
            continue
            
        all_athletes = Athlete.objects.filter(competition=event.competition)
        
        results_list = []
        for athlete in all_athletes:
            # Ищем результат этого спортсмена в этом виде
            r = Result.objects.filter(event=event, athlete=athlete).first()
            
            # Если результат есть, берем данные из него, если нет - ставим пустоту
            if r:
                attempts = [r.attempt_1, r.attempt_2, r.attempt_3, r.attempt_4, r.attempt_5, r.attempt_6]
                final_res = r.final_result
            else:
                attempts = [None, None, None, None, None, None]
                final_res = None

            results_list.append({
                'athlete_name': athlete.full_name,
                'organization': athlete.organization or '',
                'birth_year': athlete.birth_date.year if athlete.birth_date else '',
                'attempts': attempts,
                'final_result': final_res,
            })
        
        # Сортируем список: сначала те, у кого есть результат (по убыванию), потом остальные
        results_list.sort(key=lambda x: x['final_result'] if x['final_result'] else -1, reverse=True)
            
        events_data.append({
            'event': event,
            'results': results_list
        })

    categories = Event.objects.values_list('category', flat=True).distinct().order_by('category')

    context = {
        'events_data': events_data,
        'genders': ['М', 'Ж'],
        'categories': categories,
        'selected_gender': selected_gender,
        'selected_category': selected_category,
    }
    return render(request, 'results.html', context)
