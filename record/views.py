from django.http import Http404
from django.utils import timezone
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# from rest_framework.authtoken.models import Token
from .models import Record
from .serializers import RecordSerializer
from .permissions import IsOwnerOrReadonly, IsOwner
from .utils import group_records_by_date


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
    permission_classes = [IsOwner]

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
        record = self.get_object(pk)
        if record.author != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = RecordSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        record = self.get_object(pk)
        if record.author != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            record.delete()
            return Response({'message': 'Delete successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(http_method_names=["GET"])
def records_date_range_view(request):
    if request.method == "GET":
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by_date = request.query_params.get('group_by_date', 'false').lower() in [
            'true', 'yes', 't']
        is_decreasing = request.query_params.get('is_decreasing', 'false').lower() in [
            'true', 'yes', 't']
        if not start_date or not end_date:
            return Response({'error': 'Both start_date and end_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        records = Record.objects.filter(
            author=request.user, date__range=[start_date, end_date]).order_by(f'{"-" if is_decreasing else ""}date')
        serializer = RecordSerializer(records, many=True)
        if records.exists():
            if group_by_date:
                group_data = group_records_by_date(serializer.data)
                return Response(group_data, status=status.HTTP_200_OK)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No record found'}, status=status.HTTP_404_NOT_FOUND)
