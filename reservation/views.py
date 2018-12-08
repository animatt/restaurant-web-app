import pprint
import json
import datetime
import sys
import os
import re

from django.utils import timezone
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

import django.db as db
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db import transaction, connection
from django.db.utils import DatabaseError
from timeline.models import Reservation

from reservation.test_utils import ConcurrencyError, TEST_SIM_RACE_CONDITION

SQL_PATH = 'reservation/sql'


def hold_seats_for_confirmation(request, num_seats_requested, start, tables):
    '''
    request: normal request object (cls)
    num_seats_requested: party size (int)
    start: datetime lacking timezone postfix (str)
    tables: list of tables (`id`, `space_type`, `loc_type`, `num_seating`)

    returns >> reservation_id

    Attempt to create a reservation for the tables in `tables`. If any of these
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
    num_menus = num_seats_requested

    for table in tables:
        loc_id, *_ = table
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
        set_vars, lock_tables = transaction_head
        cursor.execute(set_vars, params)
        cursor.execute(lock_tables.format(', '.join([str(s[0]) for s in tables])))
        tables_from_query = cursor.fetchall()

        if len(tables_from_query) < len(tables):
            e = ConcurrencyError('Tables no longer available.')
            e.tables_already_reserved = set(tables) - set(tables_from_query)
            raise e
        for query in transaction_tail:
            cursor.execute(query)

        cursor.execute('SELECT @reservation_id')
        return cursor.fetchone()[0]


def select_least_needed(request, num_seats_requested, start):
    '''
    request: request object (must contain user)
    num_seats_requested: party size (int)
    start: reservation datetime (datetime)

    returns >> seats (tuple), res_id (int)

    Get the smallest set of available tables of the same type and location
    that fullfills the reservation but exceeds in capacity the party size by
    no more than one seat. Create the reservation if it can be fulfilled,
    otherwise, throw an EOFError.
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
                            num_seats_requested,
                            start,
                            result_set,
                        )
                except ConcurrencyError as e:
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
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})

    res_id = request.session['reservation']['res_id']
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                'UPDATE timeline_reservation SET confirmed = 1 '
                f'WHERE id = {res_id}'
            )
        except DatabaseError as e:
            print(e)

    return HttpResponseRedirect(reverse('reservation:confirmation'))

def confirmation(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})

    try:
        print(request.session['reservation'])
    except KeyError:
        print('no reservation key in session')
    return render(request, 'reservation/confirmation.html', {})

def get_reservations(user_id):
    '''
    Return the reservations attached to the user identified by `user_id` in the
    form of (num_menus, res_datetime, space_name, res_id).
    '''
    with connection.cursor() as cursor:
        query_path = os.path.join(SQL_PATH, 'get_reservations.sql')
        get_reservations_query = open(query_path).read()
        cursor.execute(get_reservations_query.format(user_id))

        def func_return_type(func, new_type):
            def new_func(*args):
                obj = func(*args)
                return new_type(obj)
            return new_func

        global map
        map = func_return_type(map, list)
        res = cursor.fetchall()
        res = [map(str, r) for r in res]
        for r in res:
            r[1] = re.sub(r'^(.+) (\d\d:\d\d):.+$', r'\1T\2', r[1])

    return res

def reservations(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})
    res = get_reservations(request.user.id)
    return render(request, 'reservation/reservations.html', {'res': res})

def update_reservation(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})

    selections = []
    for k in request.POST:
        try:
            selections.append(int(k))
        except ValueError:
            pass
        else:
            print(k)

    print('selections', selections)
    for s in selections:
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    try:
                        res = Reservation.objects.get(pk=s)
                    except ObjectDoesNotExist:
                        print('Likely page refresh. `res_id` not found.')
                        continue
                    else:
                        res.delete()

                    s_new_datetime = datetime.datetime.fromisoformat(
                        request.POST[f'new-datetime{s}'] + ':00+00:00'
                    )
                    s_new_num_menus = int(request.POST[f'new-num-menus{s}'])

                    try:
                        tables, res_id = select_least_needed(
                            request,
                            s_new_num_menus,
                            s_new_datetime
                        )
                    except EOFError:
                        raise IntegrityError("No suitable accomodations.")

        except IntegrityError as e:
            return render(request, 'reservation/reservations.html', {
                'error_message': "Sorry, we're booked.",
                'res': get_reservations(request.user.id)
            })
        else:
            return render(request, 'reservation/reservations.html', {
                'success_message': "You're good to go.",
                'res': get_reservations(request.user.id)
            })

    return render(request, 'reservation/reservations.html', {
        'error_message': "You didn't make a selection!",
        'res': get_reservations(request.user.id)
    })

def cancel_reservation(request):
    if not request.user.is_authenticated:
        return render(request, 'registration/logged_out.html', {})

    res_ids = []
    for k in request.POST:
        try:
            int(k)
        except ValueError:
            pass
        else:
            res_ids.append(k)

    Reservation.objects.filter(pk__in=res_ids).delete()
    return HttpResponseRedirect(reverse('reservation:reservations'))
