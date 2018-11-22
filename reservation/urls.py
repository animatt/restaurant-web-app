from django.urls import include, path

from . import views

app_name = 'reservation'
urlpatterns = [
    path('', views.index, name='index'),
    path('request/', views.request, name='request'),
]
