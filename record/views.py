from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Record
from .serializer import RecordSerializer


class RecordList(APIView):
    """
    List all Records, or create a new Record.
    """

    def get(self, request, format=None):
        Records = Record.objects.all()
        serializer = RecordSerializer(Records, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecordDetail(APIView):
    """
    Retrieve, update or delete a Record instance.
    """

    def get_object(self, pk):
        try:
            return Record.objects.get(pk=pk)
        except Record.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        Record = self.get_object(pk)
        serializer = RecordSerializer(Record)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        Record = self.get_object(pk)
        serializer = RecordSerializer(Record, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        Record = self.get_object(pk)
        Record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
