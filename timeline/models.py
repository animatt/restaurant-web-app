from django.db import models


# Create your models here.
class Customers(models.Model):
    vip = models.BooleanField(default=False)


class Space(models.Model):
    '''
    ie. Dining room, Patio, Bar
    '''
    space_name = models.CharField(max_length=50)


class Locations(models.Model):
    '''
    ie. Booth, Table, Standing table
    '''
    loc_type = models.CharField(max_length=50)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)


class Reservations(models.Model):
    num_drink_menus = models.IntegerField(default=0)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    res_datetime = models.DateTimeField('date and of reservation')
    res_duration = models.IntegerField(default=120)


class Transactions(models.Model):
    '''
    The act of reserving a table is recorded in a transaction.
    '''
    location = models.ForeignKey(Locations, on_delete=models.CASCADE)
    reservations = models.ForeignKey(Reservations, on_delete=models.CASCADE)
    

class Roles(models.Model):
    '''
    employee roles
    '''
    emp_role = models.CharField(max_length=10)


class Employees(models.Model):
    emp_name = models.CharField(max_length=50)
    emp_sex = models.CharField(
        max_length=6,
        choices=[('M', 'male'), ('F', 'female')]
    )
    emp_role = models.ForeignKey(Roles, on_delete=models.CASCADE)


class PaymentTypes(models.Model):
    pay_type = models.CharField(max_length=10)


class Payments(models.Model):
    payment = models.ForeignKey(PaymentTypes, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    ammount = models.IntegerField()
