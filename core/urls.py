from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('judge/', views.judge_input, name='judge_input'),
    path('results/', views.spectator_results, name='spectator_results'),
    path('results/ajax/', views.spectator_results_ajax, name='spectator_results_ajax'), # НОВЫЙ МАРШРУТ
    path('export/<int:event_id>/', views.export_excel, name='export_excel'),
    path('export/long-jump/<int:event_id>/', views.export_long_jump, name='export_long_jump'),
    path('api/result/', views.input_result, name='input_result'),
]
