from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ImportExcelForm

def home(request):
    return render(request, 'home.html')

def upload_excel(request):
    if request.method == "POST":
        form = ImportExcelForm(request.POST, request.FILES)
        if form.is_valid():
            count = form.save()
            messages.success(request, f"Успешно загружено {count} участников! Вернитесь в админку.")
            return redirect('admin:core_athlete_changelist')
    else:
        form = ImportExcelForm()
    
    return render(request, 'upload_excel.html', {'form': form})
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ApiKey, Result, Event, Athlete

@csrf_exempt
def input_result(request):
    if request.method == "POST":
        key = request.headers.get("X-Api-Key")
        try:
            api_key = ApiKey.objects.get(key=key, is_active=True)
        except ApiKey.DoesNotExist:
            return JsonResponse({"error": "Неверный или неактивный ключ"}, status=403)

        athlete_id = request.POST.get("athlete_id")
        value = request.POST.get("value")
        
        event = api_key.event
        if not event:
            return JsonResponse({"error": "Ключ не привязан к виду"}, status=400)

        result, _ = Result.objects.update_or_create(
            event=event,
            athlete_id=athlete_id,
            defaults={"final_result": value, "entered_by_api": True}
        )
        return JsonResponse({"status": "ok", "id": result.id})
    
    return JsonResponse({"error": "Метод не разрешен"}, status=405)
