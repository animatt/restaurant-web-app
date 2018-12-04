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
from django.db import IntegrityError
from django.db import transaction, connection
from timeline.models import Reservation

from reservation.test_utils import TEST_SIM_RACE_CONDITION

SQL_PATH = 'reservation/sql'


def hold_seats_for_confirmation(request, seats, start):
    '''
    request: normal request object
    seats: list of seats (`id`, `space_type`, `loc_type`, `num_seating`)
    start: datetime lacking timezone postfix

    returns >> reservation_id

    Attempt to create a reservation for the seats in `seats`. If any of these
    seats cannot be reserved, throw `IntegrityError` and cancel the
    reservation.
    '''
    transaction_fragment_path = os.path.join(
        SQL_PATH, 'set_reservation_fragment.sql'
    )

    transaction_fragment = open(transaction_fragment_path, 'r').readlines()
    transaction_head = transaction_fragment[:2]
    transaction_tail = transaction_fragment[2:]

    res_datetime = str(start)
    num_menus = len(seats)

    for seat in seats:
        loc_id, *_ = seat
        transaction_tail.append(
            f'INSERT INTO timeline_transaction (location_id, reservation_id)'
            f' VALUES ({loc_id}, @reservation_id);'
        )

    params = [
        request.user.id,
        request.user.get_full_name(),
        num_menus,
        res_datetime.split('+')[0],
    ]

    with connection.cursor() as cursor:
        set_vars, lock_seats = transaction_head
        cursor.execute(set_vars, params)
        cursor.execute(lock_seats.format(', '.join([str(s[0]) for s in seats])))
        seats_from_query = cursor.fetchall()

        if len(seats_from_query) < num_menus:
            class ConcurrencyError(IntegrityError):
                tables_already_reserved = set(seats) - set(seats_from_query)
            raise ConcurrencyError('Seats no longer available.')
        for query in transaction_tail:
            cursor.execute(query)

        cursor.execute('SELECT @reservation_id')
        return cursor.fetchone()[0]


def select_least_needed(request, num_seats_requested, start):
    '''
    request: normal request object
    num_seats_requested: party size
    start: reservation datetime

    returns >> seats (tuple), res_id (int)

    Get the smallest set of available tables of the same type and location
    that fullfills the reservation but exceeds in capacity the party size by
    no more than one seat. If the reservation can't be fulfilled, throw an
    EOFError.
    '''
    size_of_table_set = 0
    tables_remaining_after_race = None
    sql_fname = 'select_least_needed_from_available.sql'

    select_least_needed_query = open(os.path.join(SQL_PATH, sql_fname)).read()

    end = start + datetime.timedelta(hours=1)
    with connection.cursor() as cursor:
        cursor.execute('SET @start = %s, @end = %s', [start, end])
        cursor.execute(select_least_needed_query)
        current_space = None
        current_loc_type = None
        result_set = []

        sql_results = cursor.fetchall()
        pprint.pprint(sql_results)

        n = len(sql_results)
        pos = 0
        while pos < n:
            row = sql_results[pos]
            loc_id, space, loc_type, num_seats = row

            if current_space != space or current_loc_type != loc_type:
                section_start = pos
                size_of_table_set = 0
                current_space = space
                current_loc_type = loc_type
                result_set = []
                tables_not_available_after_race = None

            if ((size_of_table_set < num_seats_requested
                 and
                 size_of_table_set + num_seats <= num_seats_requested + 1)
                and
                (tables_not_available_after_race is None
                 or
                 sql_results[pos] not in tables_not_available_after_race)):
                size_of_table_set += num_seats
                result_set.append(row)
            if (num_seats_requested
                <= size_of_table_set
                <= num_seats_requested + 1):

                try:
                    TEST_SIM_RACE_CONDITION()
                except:
                    pass

                try:
                    with transaction.atomic():
                        res_id = hold_seats_for_confirmation(
                            request,
                            result_set,
                            start
                        )
                except IntegrityError as e:
                    tables_not_available_after_race = e.tables_already_reserved

                    res = (str(r[0]) for r in tables_not_available_after_race)
                    print(f"({', '.join(res)}) reserved by another customer")

                    pos = section_start - 1
                    size_of_table_set = 0
                    result_set = []
                else:
                    break
            pos += 1

        if num_seats_requested <= size_of_table_set <= num_seats_requested + 1:
            return result_set, res_id
        else:
            raise EOFError("No suitable table arrangement found.")


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

    if start < timezone.now():
        return render(request, 'reservation/index.html', {
            'error_message': "Please select future accommodations."
        })
    try:
        seats, res_id = select_least_needed(
            request, num_seats_requested, start
        )
    except EOFError as e:
        print(e)
        return render(request, 'reservation/index.html', {
            'could_not_complete': (
                "Sorry. We're all booked! Please try another reservation.")})

    request.session['reservation'] = {
        'res_id': res_id,
        'seats': seats,
        'datetime': str(start),
        'num_menus': num_seats_requested
    }
    
    template = loader.get_template('reservation/request.html')
    return HttpResponse(template.render({'seats': seats}, request))


def preconfirmation(request):
    
    return HttpResponse('OK')

def confirmation(request):
    try:
        print(request.session['reservation'])
    except KeyError:
        print('no reservation key in session')
    return render(request, 'reservation/confirmation.html', {})
