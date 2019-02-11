from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as log

import json

# Create your views here.
def check_credentials(request):
    if request.method == 'POST':
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
        log(request, user)
        return HttpResponse('The username and password are correct')
        # if user is not None:
        # cookie is sessionid    if request.method != 'GET':

    return HttpResponse(json.dumps({
        'loggedIn': request.user.is_authenticated,
        'userName': request.user.username
    }))
