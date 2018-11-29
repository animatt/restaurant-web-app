import datetime
import pprint

from django.utils.html import escape
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from fake_data import fake_data_generator


def signin_user(test_obj):
    user = User.objects.create(username='typical_user', password='open')
    test_obj.client.force_login(user, backend=None)

# Create your tests here.
class ReservationModelTests(TestCase):
    pass


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
        self.assertContains(response, escape("We don't have tables available"))

    def test_select_reservation_open_tables(self):
        '''
        Attempting to make a reservation for a time when tables are available
        should succeed.
        '''
        fake_data_generator.create_data(num_res=0)
        signin_user(self)
        response = self.client.post(reverse('reservation:request'), {
            'num_guests': 1,
            'date': (
                datetime.datetime.now() + datetime.timedelta(days=10)
            ).strftime('%Y-%m-%dT%H:%M')
        })
        pprint.pprint(response.getvalue().decode())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, escape('Would you like us to reserve these seats?')
        )
