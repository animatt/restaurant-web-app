from django.urls import include, path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('credentials', views.check_credentials, name="check_crendentials"),
]
