import re
import pprint
import datetime
import os

from reservation.test_utils import ConcurrencyError, TEST_SIM_RACE_CONDITION
from django.db import transaction, connection

SQL_PATH = 'reservation/sql/sql'

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
    tables_not_available_after_race = []
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

    section_start = 0
    while True:
        section_start, tables = _find_smallest_candidate(
            sql_results,
            num_seats_requested,
            section_start,
            tables_not_available_after_race
        )

        TEST_SIM_RACE_CONDITION()

        try:
            with transaction.atomic():
                res_id = _hold_seats_for_confirmation(
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

    return result_set, res_id


def _hold_seats_for_confirmation(request, num_seats_requested, start, tables):
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


def _scan(
        tables,
        num_seats_requested,
        pos,
        tables_not_available_after_race):
    '''
    tables: list of tables (table_id, space_name, table_type, num_seats)
    num_seats_requested: obv (int)
    pos: where to start the search (int)

    returns >> (found (bool), section_transition (bool), table_set (list))

    Scan tables starting at pos and ending when the next_section is reached.
    Returns the start of the current section as well as other info.
    '''
    table_set_size = 0
    table_set = []
    current_space_n_type = tables[pos][1:3]
    if pos == len(tables) - 1 or tables[pos + 1][1:3] != current_space_n_type:
        entering_new_section = True
    else:
        entering_new_section = False

    while pos < len(tables) and tables[pos][1:3] == current_space_n_type:
        table = tables[pos]
        if (table[3] + table_set_size <= num_seats_requested + 1
            and table not in tables_not_available_after_race
        ):
            table_set_size += table[3]
            table_set.append(table)
        if 0 <= table_set_size - num_seats_requested <= 1:
            return True, entering_new_section, table_set

        pos += 1

    return False, entering_new_section, None

def _find_smallest_candidate(
        tables,
        num_seats_requested,
        pos,
        tables_not_available_after_race):
    '''
    tables: sorted list of tables
    num_seats_requested: you know
    pos: position at which to start the search

    returns >> (beginning_of_section, table_set)

    Find the smallest set of tables that can seat the number of guests
    of the customer, but doesn't exceed this this number in capacity by more
    than a single seat. Throw an exception if the request cannot be 
    accomodated.
    '''
    found = False
    eof = False
    section_start = pos
    while not found and not eof:
        found, entering_new_section, table_set = _scan(
            tables, num_seats_requested, pos, []
        )
        pos += 1
        if entering_new_section:
            section_start = pos
        if pos == len(tables):
            eof = True
    if found:
        return section_start, table_set

    raise EOFError("No suitable table arrangement found.")
