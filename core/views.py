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
