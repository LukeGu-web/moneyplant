from datetime import datetime
from django.utils.timezone import make_aware
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from .models import Record, Transfer
from .serializers import RecordSerializer, TransferSerializer
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
def all_records_view(request):
    if request.method == "GET":
        book_id = request.query_params.get('book_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by_date = request.query_params.get('group_by_date', 'false').lower() in [
            'true', 'yes', 't']
        is_decreasing = request.query_params.get('is_decreasing', 'false').lower() in [
            'true', 'yes', 't']
        if not start_date or not end_date:
            return Response({'error': 'Both start_date and end_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
            end_date = make_aware(datetime.strptime(end_date, "%Y-%m-%d"))
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        records = Record.objects.filter(
            book__id=book_id, date__range=[start_date, end_date])
        transfers = Transfer.objects.filter(
            book__id=book_id, date__range=[start_date, end_date])
        record_serializer = RecordSerializer(
            records, many=True, context={'request': request})
        transfer_serializer = TransferSerializer(
            transfers, many=True, context={'request': request})

        all_records_data = record_serializer.data + transfer_serializer.data
        # sort by date
        all_records_data.sort(key=lambda r: r['date'], reverse=is_decreasing)

        if group_by_date:
            group_data = group_records_by_date(all_records_data)
            return Response(group_data, status=status.HTTP_200_OK)
        return Response(all_records_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def tax_only_records_view(request):
    if request.method == 'GET':
        book_id = request.query_params.get('book_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by_date = request.query_params.get('group_by_date', 'false').lower() in [
            'true', 'yes', 't']
        is_decreasing = request.query_params.get('is_decreasing', 'false').lower() in [
            'true', 'yes', 't']
        if not start_date or not end_date:
            return Response({'error': 'Both start_date and end_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
            end_date = make_aware(datetime.strptime(end_date, "%Y-%m-%d"))
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        records = Record.objects.filter(
            book__id=book_id, date__range=[start_date, end_date], is_marked_tax_return=True).order_by(f'{"-" if is_decreasing else ""}date')

        serializer = RecordSerializer(records, many=True)

        if records.exists():
            if group_by_date:
                group_data = group_records_by_date(serializer.data)
                return Response(group_data, status=status.HTTP_200_OK)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No record found'}, status=status.HTTP_404_NOT_FOUND)
