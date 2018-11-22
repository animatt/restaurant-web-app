from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('floorplan/<space>', views.floorplan, name='floorplan'),
    path('chart/', views.chart, name='chart'),
]
