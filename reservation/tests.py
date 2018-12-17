import pytz
import datetime
import pprint

from django.utils.html import escape
from django.utils import timezone
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError

from unittest import mock

from timeline.models import Location, Space, Reservation, Customer
from fake_data import fake_data_generator as fdg

from .sql.utils import (
    _hold_seats_for_confirmation,
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

def signin_user(test_obj):
    user = User.objects.create(username="Testy", password='testypasswd')
    test_obj.client.force_login(user, backend=None)
    user.first_name = "Testy"
    user.last_name = "Smith"
    user.save()
    return user

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

        res_id = _hold_seats_for_confirmation(self.request, 1, start, [seat])
        reservations = Reservation.objects.all()

        self.assertIsNotNone(res_id)
        self.assertEqual(res_id, reservations.first().id)
        self.assertEqual(reservations.first().confirmed, 0)

    def test_hold_seats_for_confirmation_concurrent_block(self):
        '''
        If two database connections request a reservation on an intersecting
        set of locations, the leading request should succeed, and the lagging
        request should receive a `ConcurrencyError`. This function ensures that
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
            res_id = _hold_seats_for_confirmation(self.request, 2, start, seats)
        
        self.assertTrue('Tables no longer available.' in str(context.exception))

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
            't@test.com',
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
            reservation = Reservation.objects.all().first()
            self.assertIsNotNone(reservation)
            self.assertEqual(res_id, reservation.id)
            self.assertEqual(num_seats_requested, reservation.num_menus)

            Reservation.objects.get(pk=res_id).delete()

    def test_select_least_needed_tables_available_special_case(self):
        _user = User.objects.create_user(
            'Testy',
            't@test.com',
            'testyboy5'
        )
        _user.first_name = 'Testy'
        _user.last_name = 'Smith'
        _user.save()

        fdg.drop_make_spaces()
        space = Space.objects.all().first()
        create_6_seater = create_loc_factory('Standing', 6, space)
        create_4_seater = create_loc_factory('Standing', 4, space)

        create_6_seater()
        create_4_seater()
        create_4_seater()

        class request:
            user = _user
        start = timezone.now() + datetime.timedelta(hours=1)

        num_seats_requested = 8
        tables, res_id = select_least_needed(
            request,
            num_seats_requested,
            start
        )
        reservation = Reservation.objects.get(pk=res_id)
        self.assertIsNotNone(reservation)
        self.assertEqual(res_id, reservation.id)
        self.assertEqual(num_seats_requested, reservation.num_menus)

    
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
        mock_capture = 'reservation.sql.utils.TEST_SIM_RACE_CONDITION'
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
        
class ReservationUpdateReservationViewTests(TestCase):
    def test_update_reservation_no_change(self):
        '''
        If the customer requests reservations, but doesn't pick new values,
        don't alter their reservations.
        '''
        space = Space.objects.create(space_name='Patio')
        table = Location.objects.create(
            loc_type='Standing',
            num_seating=2,
            space=space
        )

        class request:
            user = signin_user(self)

        RES_DATETIME = timezone.now() + datetime.timedelta(days=1)
        NUM_MENUS = 1
        ID = request.user.id

        _, res_id = select_least_needed(request, NUM_MENUS, RES_DATETIME)

        form_res_datetime = ':'.join(
            str(RES_DATETIME).split('+')[0].split(':')[:-1])
        form_num_menus = str(NUM_MENUS)
        form_id = str(res_id)

        POST = {
            form_id: 'on',
            f'new-datetime{form_id}': form_res_datetime,
            f'new-num-menus{form_id}': form_num_menus
        }

        response = self.client.post(
            reverse('reservation:update'), POST, follow=True
        )

        res = Reservation.objects.all().first()
        cus = Customer.objects.all().first()

        form_res_datetime_dt = datetime.datetime.fromisoformat(
            form_res_datetime).replace(tzinfo=pytz.UTC)

        self.assertEqual(cus.app_id, ID)
        self.assertEqual(res.res_datetime, form_res_datetime_dt)
        self.assertEqual(res.num_menus, NUM_MENUS)
        self.assertContains(response, escape("You're good to go."))

    def test_update_reservation_arrangements_found(self):
        '''
        If the customer requests a new reservation and they can be accomodated,
        their reservation should be changed and an appropriate message should
        be displayed.
        '''
        space = Space.objects.create(space_name='Patio')
        make_2_seat_standing_patio = create_loc_factory(
            loc_type='Standing', num_seating=2, space=space)
        table1 = make_2_seat_standing_patio()
        table2 = make_2_seat_standing_patio()

        class request:
            user = signin_user(self)

        RES_DATETIME = timezone.now() + datetime.timedelta(days=1)
        NUM_MENUS = 1
        ID = request.user.id

        _, new_res_id = select_least_needed(request, NUM_MENUS, RES_DATETIME)

        NEW_RES_DATETIME = timezone.now() + datetime.timedelta(days=2)
        NEW_NUM_MENUS = 3
        NEW_ID = ID  # this is the customer's "app_id" which shouldn't change

        form_res_datetime = ':'.join(
            str(NEW_RES_DATETIME).split('+')[0].split(':')[:-1])
        form_num_menus = str(NEW_NUM_MENUS)
        form_id = str(new_res_id)

        POST = {
            form_id: 'on',
            f'new-datetime{form_id}': form_res_datetime,
            f'new-num-menus{form_id}': form_num_menus
        }

        response = self.client.post(
            reverse('reservation:update'), POST, follow=True
        )

        res = Reservation.objects.all().first()
        cus = Customer.objects.all().first()

        form_res_datetime_dt = datetime.datetime.fromisoformat(
            form_res_datetime).replace(tzinfo=pytz.UTC)

        self.assertEqual(cus.app_id, ID)
        self.assertEqual(res.res_datetime, form_res_datetime_dt)
        self.assertEqual(res.num_menus, NEW_NUM_MENUS)
        self.assertContains(response, escape("You're good to go."))

    def test_update_reservation_arrangements_found(self):
        '''
        If the customer requests reservations but they cannot be accomodated,
        their reservations should remain unchanged.
        '''
        pass


class ReservationIndexViewTests(TestCase):
    def assemble_session(self, dictionary):
        '''
        Update session variables for use in test templates. Adapted from
        https://groups.google.com/forum/#!topic/django-users/Unji8rnm2hM
        '''
        import importlib
        from django.conf import settings
        engine = importlib.import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        session = self.client.session
        session.update(dictionary)
        session.save()
        # and now remember to re-login!

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
        Trying to make a reservation when no tables are available returns you 
        to the results page and displays an appropriate message.
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

    def test_confirm_reservation(self):
        '''
        Confirming reservations should result in an appropriate message being
        displayed.
        '''
        res_datetime_raw = timezone.now() + datetime.timedelta(days=1)
        res_datetime = str(res_datetime_raw).split('+')[0]

        table_id = None
        table_space = 'Patio'
        table_type = None
        num_seats = None
        
        reservation = {
            'seats': [(table_id, table_space, table_type, num_seats)],
            'datetime': res_datetime
        }

        self.assemble_session({'reservation': reservation})
        signin_user(self)

        response = self.client.get(reverse('reservation:confirmation'), {})
        expected_msg = 'Your seats at the {} have been reserved for {}.'

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape(expected_msg.format(table_space, res_datetime))
        )

class ReservationReservationsViewTests(TestCase):
    pass
