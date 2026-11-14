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
