from django.contrib import admin

from .models import Employee, Reservation

# Register your models here.
admin.site.register(Employee)
admin.site.register(Reservation)
