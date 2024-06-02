from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Record

# Create your views here.


@api_view(['GET'])
def getRecords(request):
    data=Record.objects.all()
    return Response(data)


def index(request, id):
    print(id)
    return HttpResponse("test record page")


def second(request):
    return HttpResponse("second record page")
