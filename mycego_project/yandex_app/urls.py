from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.files, name='files'),
    path('download/', views.download_file, name='download'),
]