from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# from rest_framework.authtoken.models import Token
from .models import Record
from .serializers import RecordSerializer
from .permissions import IsOwnerOrReadonly


class RecordList(APIView):
    """
    List all Records, or create a new Record.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        records = Record.objects.filter(author=request.user)
        serializer = RecordSerializer(records, many=True)
        if records.exists():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No record found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, format=None):
        serializer = RecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecordDetail(APIView):
    """
    Retrieve, update or delete a Record instance.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Record.objects.get(pk=pk)
        except Record.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        record = self.get_object(pk)
        if record.author == request.user:
            serializer = RecordSerializer(record)
            return Response(serializer.data)
        else:
            return Response({'error': 'No record found'}, status=status.HTTP_404_NOT_FOUND)

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
