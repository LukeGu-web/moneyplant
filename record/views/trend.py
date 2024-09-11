from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth
from book.models import Book
from record.models import Record
from datetime import datetime, timedelta
from calendar import monthrange


class RecordTrendView(generics.ListAPIView):
    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')
        queryset = Record.objects.all()

        if book_id:
            try:
                queryset = queryset.filter(book_id=book_id)
            except Book.DoesNotExist:
                raise ValidationError({"Book not found"})
        return queryset

    def list(self, request, *args, **kwargs):
        filter_type = request.query_params.get('type', 'balance')
        time_frame = request.query_params.get('time_frame', '')

        queryset = self.get_queryset()

        if filter_type in ['income', 'expense']:
            queryset = queryset.filter(type=filter_type)

        # Parse time_frame
        if '@' in time_frame:
            year, week = time_frame.split('@')
            return self.get_week_data(queryset, filter_type, int(year), int(week))
        elif '-' in time_frame:
            year, month = time_frame.split('-')
            return self.get_month_data(queryset, filter_type, int(year), int(month))
        elif time_frame.isdigit():
            return self.get_year_data(queryset, filter_type, int(time_frame))
        else:
            raise ValidationError({"detail": "Invalid time_frame format"})

    def get_year_data(self, queryset, filter_type, year):
        queryset = queryset.filter(date__year=year)
        data = queryset.annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(value=Sum('amount')) \
            .order_by('month')

        data_dict = {item['month'].month: item['value'] for item in data}
        result = []
        running_balance = 0

        for month in range(1, 13):
            value = data_dict.get(month, 0)
            if filter_type == 'balance':
                running_balance += value
                result.append({
                    'date': f"{year}-{month:02d}",
                    'value': abs(running_balance)
                })
            else:
                result.append({
                    'date': f"{year}-{month:02d}",
                    'value': abs(value)
                })

        return Response(result)

    def get_month_data(self, queryset, filter_type, year, month):
        queryset = queryset.filter(date__year=year, date__month=month)
        data = queryset.annotate(day=TruncDate('date')) \
            .values('day') \
            .annotate(value=Sum('amount')) \
            .order_by('day')

        _, days_in_month = monthrange(year, month)
        data_dict = {item['day'].day: item['value'] for item in data}
        result = []
        running_balance = 0

        for day in range(1, days_in_month + 1):
            value = data_dict.get(day, 0)
            if filter_type == 'balance':
                running_balance += value
                result.append({
                    'date': f"{year}-{month:02d}-{day:02d}",
                    'value': abs(running_balance)
                })
            else:
                result.append({
                    'date': f"{year}-{month:02d}-{day:02d}",
                    'value': abs(value)
                })

        return Response(result)

    def get_week_data(self, queryset, filter_type, year, week):
        start_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
        end_date = start_date + timedelta(days=6)
        queryset = queryset.filter(date__range=[start_date, end_date])
        data = queryset.annotate(day=TruncDate('date')) \
            .values('day') \
            .annotate(value=Sum('amount')) \
            .order_by('day')

        data_dict = {item['day']: item['value'] for item in data}
        result = []
        running_balance = 0

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            value = data_dict.get(current_date, 0)
            if filter_type == 'balance':
                running_balance += value
                result.append({
                    'date': current_date.strftime("%Y-%m-%d"),
                    'value': abs(running_balance)
                })
            else:
                result.append({
                    'date': current_date.strftime("%Y-%m-%d"),
                    'value': abs(value)
                })

        return Response(result)
