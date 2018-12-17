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

from reservation.sql.utils import get_reservations, select_least_needed

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
