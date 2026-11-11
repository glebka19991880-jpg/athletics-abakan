from django.contrib import admin
from .models import Competition, Athlete, Event, Result, ApiKey

admin.site.register(Competition)
admin.site.register(Athlete)
admin.site.register(Event)
admin.site.register(Result)
admin.site.register(ApiKey)

admin.site.site_header = "Результаты соревнований"
admin.site.site_title = "Управление"
