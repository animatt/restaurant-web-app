from django.urls import include, path

from . import views

app_name = 'reservation'
urlpatterns = [
    path('', views.index, name='index'),
    path('request/', views.request, name='request'),
    path('preconfirmation/', views.preconfirmation, name='preconfirmation'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('reservations/', views.reservations, name='reservations'),
    path('update/', views.update_reservation, name='update'),
    path('cancel/', views.cancel_reservation, name='cancel'),
]
