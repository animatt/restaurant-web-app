import pprint
import json
import datetime
import sys
import os

from django.utils import timezone
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

import django.db as db
from django.db import connection
from timeline.models import Reservation

SQL_PATH = 'reservation/sql'

def select_least_needed(num_seats_requested, start, end):
    '''
    Get the smallest set of available tables of the same type and location
    that fullfills the reservation but exceeds in capacity the party size by
    no more than one seat. If no such arrangement is found, throw an
    EOFError.
    '''
    size_of_table_set = 0
    sql_fname = 'select_least_needed_from_available.sql'

    select_least_needed_query = open(os.path.join(SQL_PATH, sql_fname)).read()

    with connection.cursor() as cursor:
        cursor.execute(select_least_needed_query, [start, end])
        current_space = None
        current_loc_type = None
        result_set = []

        sql_results = cursor.fetchall()
        # pprint.pprint(sql_results)

        for row in sql_results:
            loc_id, space, loc_type, num_seats = row
            if current_space != space or current_loc_type != loc_type:
                size_of_table_set = 0
                current_space = space
                current_loc_type = loc_type
                result_set = []

            if size_of_table_set < num_seats_requested:
                size_of_table_set += num_seats
                result_set.append(row)
            if (num_seats_requested
                <= size_of_table_set
                <= num_seats_requested + 1):
                break

        if num_seats_requested <= size_of_table_set <= num_seats_requested + 1:
            return result_set
        else:
            raise EOFError("No suitable table arrangement found anywhere.")


# Create your views here.
def index(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})
    template = loader.get_template('reservation/index.html')
    return HttpResponse(template.render({}, request))


def request(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})

    try:
        num_seats_requested = int(request.POST['num_guests'])
        start = datetime.datetime.fromisoformat(
            request.POST['date'] + ':00+00:00'
        )
    except (KeyError, ValueError):
        return render(request, 'reservation/index.html', {
            'error_message': "You didn't select a choice.",
        })
    else:
        end = start + datetime.timedelta(minutes=90)

    if start < timezone.now():
        return render(request, 'reservation/index.html', {
            'error_message': "Please select future accommodations."
        })
    try:
        seats = select_least_needed(num_seats_requested, start, end)
    except EOFError as e:
        print(e)
        return render(request, 'reservation/index.html', {
            'could_not_complete': (
                "Sorry. We don't have tables available at the requested time "
                "for a party of this size. Please select a different "
                " reservation. Thank you!")})

    reservation_datetime = json.dumps(start, default=str)
    request.session['reservation'] = {
        'seats': seats,
        'datetime': reservation_datetime,
        'num_menus': num_seats_requested
    }

    template = loader.get_template('reservation/request.html')
    return HttpResponse(template.render({'seats': seats}, request))

def preconfirmation(request):
    transaction_fragment_path = os.path.join(
        SQL_PATH,
        'set_reservation_fragment.sql'
    )
    transaction_fragment = open(transaction_fragment_path, 'r').read()
    reservation = request.session['reservation']

    seats = reservation['seats']
    res_datetime = reservation['datetime']
    num_menus = reservation['num_menus']

    for seat in seats:
        loc_id, *_ = seat
        transaction_fragment += (
            f'  INSERT INTO timeline_transaction (location_id, reservation_id)'
            f' VALUES ({loc_id}, @reservation_id);\n'
        )
    transaction_fragment += 'COMMIT;'
    make_reservation = transaction_fragment

    params = [
        request.user.id,
        request.user.get_full_name(),
        num_menus,
        res_datetime
    ]

    with connection.cursor() as cursor:
        try:
            cursor.execute(make_reservation, params)
            results = cursor.fetchall()
        except db.OperationalError as e:
            print(e)
        except db.Error as e:
            print(e)
        finally:
            result = cursor.status_message

    return HttpResponse('OK')

def confirmation(request):
    try:
        print(request.session['reservation'])
    except KeyError:
        print('no reservation key in session')
    return render(request, 'reservation/confirmation.html', {})
