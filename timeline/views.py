from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("This is the timeline index")

def floorplan(request, space):
    return HttpResponse("This is the floorplan for blah")

def chart(request):
    return HttpResponse("This is a gantt chart")
