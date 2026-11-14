from django.urls import path
from . import views
path('api/result/', views.input_result, name='input_result'),
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('judge/', views.judge_input, name='judge_input'), # Вот эта строчка
]
path('export/<int:event_id>/', views.export_excel, name='export_excel'),
