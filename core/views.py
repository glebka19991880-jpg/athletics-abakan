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
