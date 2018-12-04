import calendar

from django.db import models


# Create your models here.
class Customer(models.Model):
    vip = models.BooleanField(default=False)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    app_id = models.IntegerField(unique=True)


class Space(models.Model):
    '''
    ie. Dining room, Patio, Bar
    '''
    space_name = models.CharField(max_length=50)


class Location(models.Model):
    '''
    ie. Booth, Table, Standing table
    '''
    loc_type = models.CharField(max_length=50)
    num_seating = models.IntegerField(default=2)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)


class Reservation(models.Model):
    num_menus = models.IntegerField(default=0)
    res_datetime = models.DateTimeField('Date and time of reservation')
    res_duration = models.IntegerField(default=120)
    res_requested = models.DateTimeField('Date and time of request')
    confirmed = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return (
            f'{self.customer.name} at {self.res_datetime.strftime("%I:%M %p")}'
            f' on {calendar.day_name[self.res_datetime.weekday()]}'
        )
    

class Transaction(models.Model):
    '''
    The act of reserving a table is recorded in a transaction.
    '''
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    

class Role(models.Model):
    '''
    employee roles
    '''
    emp_role = models.CharField(max_length=10)

    def __str__(self):
        return self.emp_role

class Employee(models.Model):
    emp_name = models.CharField(max_length=50)
    emp_sex = models.CharField(
        max_length=6,
        choices=[('M', 'male'), ('F', 'female')]
    )
    emp_role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return self.emp_name


class PaymentType(models.Model):
    pay_type = models.CharField(max_length=15)


class Payment(models.Model):
    ammount = models.IntegerField()
    payment = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
