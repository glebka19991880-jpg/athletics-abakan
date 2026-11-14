from django.urls import path
from . import views
path('api/result/', views.input_result, name='input_result'),
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
]
