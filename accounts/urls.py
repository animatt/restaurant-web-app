from django.urls import include, path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.check_credentials, name="check_crendentials"),
]
