from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('judge/', views.judge_input, name='judge_input'),
    path('export/<int:event_id>/', views.export_excel, name='export_excel'),
    path('api/result/', views.input_result, name='input_result'),
]
