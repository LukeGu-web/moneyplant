from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from record.models import Record, Transfer
from record.serializers import RecordSerializer, TransferSerializer


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
