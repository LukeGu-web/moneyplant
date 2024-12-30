from django.db.models import Sum, F, Q
from django.db.models.functions import TruncMonth
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from record.models import Record
from book.models import Book
from record.serializers import MonthlyDataSerializer


class MonthlyDataView(ListAPIView):
    serializer_class = MonthlyDataSerializer

    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')

        queryset = Record.objects.filter(
            scheduledrecord__isnull=True
        )

        if book_id:
            try:
                queryset = queryset.filter(book_id=book_id)
            except Book.DoesNotExist:
                raise ValidationError({"Book not found"})

        queryset = queryset.annotate(month=TruncMonth('date')).values('month')
        queryset = queryset.annotate(
            monthly_income=Sum('amount', filter=Q(type='income')),
            monthly_expense=Sum('amount', filter=Q(type='expense'))
        )
        queryset = queryset.order_by('month')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
