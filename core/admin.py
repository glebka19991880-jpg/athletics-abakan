from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Competition, Athlete, Event, Result, ApiKey
from .forms import ImportExcelForm

def import_excel_view(request):
    if request.method == "POST":
        form = ImportExcelForm(request.POST, request.FILES)
        if form.is_valid():
            count = form.save()
            messages.success(request, f"Успешно загружено {count} участников!")
            return redirect('admin:core_athlete_changelist')
    else:
        form = ImportExcelForm()
    
    context = {
        **admin.site.each_context(request),
        'title': 'Загрузка участников из Excel',
        'form': form,
    }
    return render(request, "admin/import_excel.html", context)

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'rank', 'organization')
    search_fields = ('full_name',)
    change_list_template = 'admin/change_list.html' # Оставляем шаблон

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-excel/', self.admin_site.admin_view(import_excel_view), name='import_excel'),
        ]
        return my_urls + urls
        
    # Добавляем кастомную кнопку через actions
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Competition)
admin.site.register(Event)
admin.site.register(Result)
admin.site.register(ApiKey)

admin.site.site_header = "Результаты соревнований"
admin.site.site_title = "Управление"
