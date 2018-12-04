import datetime
import pprint

from django.utils.html import escape
from django.utils import timezone
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError

from unittest import mock

from timeline.models import Location, Space, Reservation
from fake_data import fake_data_generator as fdg

from .views import (
    hold_seats_for_confirmation,
    select_least_needed,
)

def create_loc_factory(loc_type=None, num_seating=None, space=None):
    def create_loc(
            loc_type=loc_type,
            num_seating=num_seating,
            space=space
    ):
        table = Location.objects.create(
            loc_type=loc_type,
            num_seating=num_seating,
            space=space
        )
        return table
    return create_loc

def signin_user(test_obj, username='typical_user'):
    user = User.objects.create(username=username, password='open')
    test_obj.client.force_login(user, backend=None)

# Create your tests here.
class ReservationModelTests(TransactionTestCase):
    '''
    Might want to move the concurrency tests to there own class later.
    Inheriting from `TransactionTestCase` instead of `TestCase` seems to cause
    a classes tests to run significantly more slowly.
    '''
    def test_hold_seats_for_confirmation(self):
        '''
        Trying to reserve seats returned by `select_least_needed` should
        result, excepting concurrency issues, in a reservation being created,
        and its `id` being returned.
        '''
        # create user
        user1 = User.objects.create_user(
            'Testy', 'testy@test.com', 'testypasswd'
        )
        user1.first_name = "Testy"
        user1.last_name = "Smith"
        user1.save()

        # create mock request (the relevant part)
        class request:
            user = user1
        self.request = request

        # create fake data
        fdg.drop_make_spaces()

        seat = Location.objects.create(
            loc_type='Patio',
            num_seating=2,
            space=Space.objects.all().first()
        )
        seat = (seat.id, None, None, None)  # only care about id
        res_datetime = timezone.now() + datetime.timedelta(days=1)
        start = str(res_datetime).split('+')[0]

        res_id = hold_seats_for_confirmation(self.request, [seat], start)
        reservations = Reservation.objects.all()

        self.assertIsNotNone(res_id)
        self.assertEqual(res_id, reservations.first().id)
        self.assertEqual(reservations.first().confirmed, 0)

    def test_hold_seats_for_confirmation_concurrent_block(self):
        '''
        If two database connections request a reservation on an intersecting
        set of locations, the leading request should succeed, and the lagging
        request should receive an `IntegrityError`. This function ensures that
        the lagging request will fail with the above exception by simulating
        the effects of a race condition. It does not rely on actual
        concurrency and therefore performs no test of the database locks.
        '''
        user1 = User.objects.create_user(
            'Testy', 'testy@test.com', 'testypasswd'
        )
        user1.first_name = 'Testy'
        user1.last_name = 'Smith'
        user1.save()

        # create mock requests
        class request:
            user = user1
        self.request = request

        # create fake data
        fdg.drop_make_spaces()
        seat1 = Location.objects.create(
            loc_type='Patio',
            num_seating=2,
            space=Space.objects.all().first()
        )
        seat2 = Location.objects.create(
            loc_type='Patio',
            num_seating=2,
            space=Space.objects.all().first()
        )
        seats = [(seat1.id, None, None, None), (seat2.id, None, None, None)]

        # "reserve" `seat2` (it won't appear in `hold_seats_...`'s query)
        seat2.delete()

        res_datetime = timezone.now() + datetime.timedelta(days=1)
        start = str(res_datetime).split('+')[0]

        with self.assertRaises(IntegrityError) as context:
            res_id = hold_seats_for_confirmation(self.request, seats, start)
        
        self.assertTrue('Seats no longer available.' in str(context.exception))

    def test_select_least_needed_not_enough_tables(self):
        '''
        Ensure that `select_least_needed` raises EOFError if no set of tables
        is found such that 

            set_capacity <= `num_tables_requested` <= set_capacity + 1.

        with an appropriate message.
        '''
        _user = User.objects.create_user(
            'Testy', 'testy@test.com', 'testypasswd'
        )
        _user.first_name = 'Testy'
        _user.last_name = 'Smith'

        class request:
            user = _user
        num_seats_requested = 1
        start = timezone.now() + datetime.timedelta(hours=1)

        with self.assertRaises(EOFError) as context:
            seats, res_id = select_least_needed(
                request,
                num_seats_requested,
                start
            )

        self.assertTrue(
            'No suitable table arrangement found.' in str(context.exception)
        )

    def test_select_least_needed_tables_available_no_concurrency(self):
        '''
        Attempting to create a reservation while there are suitable 
        accomodations should result in the creation of a temporary reservation
        whose id `res_id` is returned, excepting concurrency issues.
        '''
        _user = User.objects.create_user(
            'Testy',
            't@test.com'
            'testyboy5'
        )
        _user.first_name = 'Testy'
        _user.last_name = 'Smith'
        _user.save()

        fdg.drop_make_spaces()
        seats_standing1 = Location.objects.create(
            loc_type='Standing',
            num_seating=2,
            space=Space.objects.all().first()
        )
        seats_standing2 = Location.objects.create(
            loc_type='Standing',
            num_seating=4,
            space=Space.objects.all().first()
        )

        class request:
            user = _user
        start = timezone.now() + datetime.timedelta(hours=1)

        for k in range(1, 7):
            num_seats_requested = k

            seats, res_id = select_least_needed(
                request,
                num_seats_requested,
                start
            )
            reservation_id = Reservation.objects.all().first()
            self.assertIsNotNone(reservation_id)
            self.assertEqual(res_id, reservation_id.id)

            Reservation.objects.get(pk=res_id).delete()

    
    def test_select_least_needed_tables_available_concurrency_block(self):
        '''
        If two requests for reservations at the same time on the same tables
        occur simultaneously, the lagging request should resume searching at 
        the beginning of the current space and table type. Any changes to the
        database instigated by the lagging request should be rolled back.
        '''
        _user = User.objects.create_user(
            'Testy',
            't@test.com',
            'testypass'
        )
        _user.first_name = 'Testy'
        _user.last_name = 'Smith'
        _user.save()

        class request:
            user = _user
        num_seats_requested = 9
        start = timezone.now() + datetime.timedelta(days=1)

        fdg.drop_make_spaces()
        patio = Space.objects.filter(space_name='Patio').first()
        bar = Space.objects.filter(space_name='Bar').first()

        create_patio_standing = create_loc_factory(
            loc_type='Standing',
            space=patio
        )
        table_4_seater = create_patio_standing(num_seating=4)
        table_6_seater = create_patio_standing(num_seating=6)
        table_2_seater_1 = create_patio_standing(num_seating=2)
        table_2_seater_2 = create_patio_standing(num_seating=2)

        tables, res_id = select_least_needed(
            request,
            num_seats_requested,
            start
        )

        ID = 0
        self.assertEqual(tables[0][ID], table_6_seater.id)
        self.assertEqual(tables[1][ID], table_4_seater.id)

        Reservation.objects.all().delete()

        func = Location.objects.get(pk=table_4_seater.id).delete
        mock_capture = 'reservation.views.TEST_SIM_RACE_CONDITION'
        with mock.patch(mock_capture, side_effect=func):
            tables, res_id = select_least_needed(
                request,
                num_seats_requested,
                start
            )

        self.assertEqual(len(tables), 3)
        self.assertEqual(tables[0][ID], table_6_seater.id)
        self.assertEqual(tables[1][ID], table_2_seater_1.id)
        self.assertEqual(tables[2][ID], table_2_seater_2.id)

        
class ReservationIndexViewTests(TestCase):
    def test_select_past_reservation(self):
        '''
        Trying to make a reservation in the past results in an appropriate
        message being displayed.
        '''
        signin_user(self)
        response = self.client.post(reverse('reservation:request'), {
            'num_guests': 1,
            'date': (
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).strftime('%Y-%m-%dT%H:%M')
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please select future accommodations.')

    def test_select_reservation_no_open_tables(self):
        '''
        Trying to make a reservation when no tables are available return you to
        the results page and displays an appropriate message.
        '''
        signin_user(self)
        response = self.client.post(reverse('reservation:request'), {
            'num_guests': 1,
            'date': (
                datetime.datetime.now() + datetime.timedelta(days=5)
            ).strftime('%Y-%m-%dT%H:%M')
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, escape("Sorry. We're all booked!"))

    def test_select_reservation_open_tables(self):
        '''
        Attempting to make a reservation for a time when tables are available
        should succeed.
        '''
        fdg.create_data(num_res=0)
        signin_user(self)
        response = self.client.post(reverse('reservation:request'), {
            'num_guests': 1,
            'date': (
                datetime.datetime.now() + datetime.timedelta(days=10)
            ).strftime('%Y-%m-%dT%H:%M')
        })
        # pprint.pprint(response.getvalue().decode())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape('Would you like us to reserve these seats?')
        )
