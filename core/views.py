from django.shortcuts import render
from .models import Athlete, Event

def home(request):
    return render(request, 'home.html')

def judge_input(request):
    events = Event.objects.filter(is_technical=True)
    event_id = request.GET.get('event')
    
    athletes = []
    current_event = None
    
    if event_id:
        current_event = Event.objects.get(id=event_id)
        athletes = Athlete.objects.filter(competition=current_event.competition)

    return render(request, 'judge.html', {
        'events': events,
        'athletes': athletes,
        'current_event': current_event,
    })
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ApiKey, Result

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
