import datetime
import sys
import os
import pprint

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

from django.db import connection
from timeline.models import Reservation

# Create your views here.
def index(request):
    template = loader.get_template('reservation/index.html')
    return HttpResponse(template.render({}, request))

def request(request):
    try:
        num_seats_requested = int(request.POST['num_guests'])
        start = datetime.datetime.fromisoformat(request.POST['date'])
    except (KeyError, ValueError):
        return render(request, 'reservation/index.html', {
            'error_message': "You didn't select a choice.",
        })
    else:
        end = start + datetime.timedelta(minutes=90)

    sql_path = 'reservation/sql'
    tables_available_query = open(os.path.join(
        sql_path, 'check_availability.sql')).read()

    with connection.cursor() as cursor:
        cursor.execute(tables_available_query, [start, end])
        (num_seats_available,) = cursor.fetchone()

    if num_seats_available < num_seats_requested:
        return render(request, 'reservation/index.html', {
            'could_not_complete': ("Sorry. We do not have space available "
                                   "at this time for a party of this size. "
                                   "Please select another reservation.")
            })

    # num_of_each_size_type_query = open(os.path.join(
    #     sql_path, 'number_of_each_type.sql')).read()

    # with connection.cursor() as cursor:
    #     cursor.execute(num_of_each_size_type_query, [start, end])
    #     num_of_each_size_type = cursor.fetchall()
    #     print(num_of_each_size_type)

    select_least_needed_query = open(os.path.join(
        sql_path, 'select_least_needed_from_available.sql')).read()

    with connection.cursor() as cursor:
        cursor.execute(select_least_needed_query, [start, end])
        current_space = current_loc_type = None
        result_set = []

        results = cursor.fetchall()
        pprint.pprint(results)

        for row in results:
            loc_id, space, loc_type, num_seats = row
            if current_space != space or current_loc_type != loc_type:
                size_of_table_set = 0
                current_space = space
                current_loc_type = loc_type
                result_set = []

            if size_of_table_set < num_seats_requested:
                size_of_table_set += num_seats
                result_set.append(row)
            elif size_of_table_set <= num_seats_requested + 1:
                break

        if num_seats_requested <= size_of_table_set <= num_seats_requested + 1:
            pass
        else:
            raise EOFError("No suitable table arrangement found anywhere.")

        print(result_set)
    template = loader.get_template('reservation/request.html')
    return HttpResponse(template.render({}, request))
