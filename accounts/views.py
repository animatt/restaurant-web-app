from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate

import json

# Create your views here.
def check_credentials(request):
    if request.method != 'GET':
        return HttpResponse('No')
    
    return HttpResponse(json.dumps({
        'loggedIn': request.user.is_authenticated,
        'userName': request.user.username
    }))

def login(request):
    if request.method != 'POST':
        return HttpResponse('No')
    body = json.loads(request.body)
    try:
        username = body['username']
        passwd = body['passwd']
    except KeyError:
        return HttpResponse('Incorrect params')

    user = request.user if request.user.is_authenticated else (
        authenticate(username=username, password=passwd)
    )
    if not user:
        return HttpResponse('The username and password are not correct')
    return HttpResponse('The username and password are correct')
    # if user is not None:
