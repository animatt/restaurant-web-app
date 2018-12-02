import faker
import random
import datetime
import pprint

import timeline.models

from django.utils import timezone

fake_factory = faker.Faker()

RES_LEN = 120  # reservation length minutes

classes = {
    name: cls for (name, cls) in timeline.models.__dict__.items()
    if isinstance(cls, type)
}

random.seed(10)

def drop_make_customers(num=25):
    '''
    truncate customers, then repopulate it.
    '''
    Customer = classes['Customer']
    Customer.objects.all().delete()
    for _ in range(num):
        c = Customer(
            vip=random.choice([True, False]),
            name=fake_factory.name(),
            phone=fake_factory.phone_number(),
            app_id=random.randint(1,1e6)
        )
        c.save()

def drop_make_spaces():
    '''
    make a few hard coded spaces.
    '''
    Space = classes['Space']
    Space.objects.all().delete()

    Space(space_name='Patio').save()
    Space(space_name='Dinning_room').save()
    Space(space_name='Bar').save()

def drop_make_locations(num=40):
    '''
    make tables, booths, etc.
    '''
    Location = classes['Location']
    Location.objects.all().delete()

    possible_spaces = classes['Space'].objects.all()

    for _ in range(num):
        loc = Location(
            loc_type=random.choice(['Booth', 'Table', 'Bar']),
            space=random.choice(possible_spaces),
            num_seating=2 * random.randint(1, 3)
        )
        loc.save()


def drop_make_roles():
    '''
    make roles for employees
    '''
    Role = classes['Role']
    Role.objects.all().delete()

    Role(emp_role='Bartender').save()
    Role(emp_role='Server').save()
    Role(emp_role='Chef').save()

def drop_make_employees(num=10):
    '''
    make some employees.
    '''
    Employee = classes['Employee']
    possible_roles = classes['Role'].objects.all()

    Employee.objects.all().delete()
    for _ in range(num):
        e = Employee(
            emp_name=fake_factory.name(),
            emp_sex=random.choice(['M', 'F']),
            emp_role=random.choice(possible_roles)
        )
        e.save()

def drop_make_reservations(num=40):
    Reservation = classes['Reservation']
    Reservation.objects.all().delete()

    possible_customers = classes['Customer'].objects.all()

    for ii in range(num):
        r = Reservation(
            num_menus=random.randint(0, 10),
            customer=random.choice(possible_customers),
            res_datetime=(
                timezone.now() + datetime.timedelta(minutes=ii * RES_LEN)
            ),
            res_duration=100 + random.randint(0, 20)
        )
        r.save()

def drop_make_payment_types():
    '''
    make payment types, ie. ccard, debit...
    '''
    PaymentType = classes['PaymentType']
    PaymentType.objects.all().delete()

    PaymentType(pay_type='credit_card').save()
    PaymentType(pay_type='debit_card').save()
    PaymentType(pay_type='check').save()
    PaymentType(pay_type='cash').save()

def drop_make_payments():
    '''
    make records of payments associated with reservations
    '''
    Payment = classes['Payment']
    Payment.objects.all().delete()

    payment_types = classes['PaymentType'].objects.all()
    reservations = classes['Reservation'].objects.all()
    employees = classes['Employee'].objects.all()

    for res in reservations:
        n_menus = res.num_menus
        mean_tot = n_menus * 30

        p = Payment(
            ammount=mean_tot + n_menus * random.randint(0, 15),
            payment=random.choice(payment_types),
            reservation=res,
            employee=random.choice(employees)
        )
        p.save()

def drop_make_transactions():
    '''
    make the transactions that record table reservations
    '''
    Transaction = classes['Transaction']
    Transaction.objects.all().delete()

    possible_locations = classes['Location'].objects.all()
    reservations = classes['Reservation'].objects.all()

    for res in reservations:
        t = Transaction(
            location=random.choice(possible_locations),
            reservations=res
        )
        t.save()

    # for res in reservations:
    #     if random.choice([True, False], [8, 2]):
    #         continue
    #     t = Transaction


#### running from $ python manage.py shell
#### >>> exec(open('fake_data/fake_data_generator.py').read())
#### :(

def create_data(num_customers=25, num_locs=40, num_emps=10, num_res=40):
    print('begin')
    drop_make_spaces()
    drop_make_locations(num_locs)
    drop_make_roles()
    # drop_make_customers(num_customers)
    drop_make_employees(num_emps)
    # drop_make_reservations()
    drop_make_payment_types()
    drop_make_payments()
    # drop_make_transactions()
    print('done')


if __name__ == '__main__':
    create_data()
