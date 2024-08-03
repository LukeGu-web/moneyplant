from django.http import Http404
from django.utils import timezone
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
# from rest_framework.authtoken.models import Token
from .models import Record, Transfer
from .serializers import RecordSerializer, TransferSerializer
from .permissions import IsOwnerOrReadonly, IsOwner
from .utils import group_records_by_date


class RecordList(generics.ListCreateAPIView):
    """
    List all Records, or create a new Record.
    """
    permission_classes = [IsAuthenticated]

    queryset = Record.objects.all()
    serializer_class = RecordSerializer


class RecordDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Record instance.
    """
    permission_classes = [IsAuthenticated]

    queryset = Record.objects.all()
    serializer_class = RecordSerializer


class TransferList(generics.ListCreateAPIView):
    """
    List all Transfers, or create a new Transfer.
    """
    permission_classes = [IsAuthenticated]

    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer


class TransferDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Transfer instance.
    """
    permission_classes = [IsAuthenticated]

    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer


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
