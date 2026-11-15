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
    
    # ИСПРАВЛЕНИЕ: Берем только тех, кто заявлен в этом виде
    results_qs = Result.objects.filter(event=current_event).select_related('athlete')
    athletes = [r.athlete for r in results_qs]

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

        result, created = Result.objects.get_or_create(
            event_id=current_event.id,
            athlete_id=athlete_id,
            defaults={'final_result': 0.0, 'assigned_rank': '', 'place': None}
        )

        for i in range(1, 7):
            val = request.POST.get(f'attempt_{i}')
            if val is not None and str(val).strip() != '':
                setattr(result, f'attempt_{i}', parse_float(val))

        attempts = [result.attempt_1, result.attempt_2, result.attempt_3, result.attempt_4, result.attempt_5, result.attempt_6]
        valid_attempts = [a for a in attempts if a and a > 0]
        result.final_result = max(valid_attempts) if valid_attempts else 0.0
        result.save()

        messages.success(request, 'Результат сохранен!')

        if 'next_athlete' in request.POST:
            current_index = next((i for i, a in enumerate(athletes) if str(a.id) == str(athlete_id)), -1)
            if current_index != -1 and current_index + 1 < len(athletes):
                next_id = athletes[current_index + 1].id
                return redirect(f'/judge/?token={token}&event={current_event.id}&athlete_id={next_id}')
            else:
                if athletes:
                    return redirect(f'/judge/?token={token}&event={current_event.id}&athlete_id={athletes[0].id}')

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
