from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from collections import defaultdict
from itertools import cycle
from record.models import Record
from django.db.models import Q
from datetime import datetime, timedelta
import re
import calendar

colors = ("#519DE9", "#7CC674", "#73C5C5", "#8481DD", "#F6D173", "#EF9234", "#A30000", "#D2D2D2",
          "#0066CC", "#4CB140", "#009596", "#5752D1", "#F4C145", "#EC7A08", "#7D1007", "#B8BBBE",
          "#004B95", "#38812F", "#005F60", "#3C3D99", "#F0AB00", "#C46100", "#470000", "#8A8D90",
          "#002F5D", "#23511E", "#003737", "#2A265F", "#C58C00", "#8F4700", "#2C0000", "#6A6E73",
          "#8BC1F7", "#BDE2B9", "#A2D9D9", "#B2B0EA", "#F9E0A2", "#F4B678", "#C9190B", "#F0F0F0")


class CategoriedRecordView(generics.ListAPIView):

    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')
        record_type = self.request.query_params.get('type')
        timeframe = self.request.query_params.get('timeframe')

        filters = Q()

        if book_id:
            filters &= Q(book_id=book_id)

        if record_type:
            if record_type not in ['income', 'expense']:
                raise ValidationError(
                    {"detail": "Invalid type. Must be 'income' or 'expense'."})
            filters &= Q(type=record_type)
        else:
            raise ValidationError(
                {"detail": "Type parameter is required. Must be 'income' or 'expense'."})

        if timeframe:
            filters &= self.build_timeframe_filter(timeframe)

        # Add the exclusion of ScheduledRecord to the filters
        filters &= Q(scheduledrecord__isnull=True)
        return Record.objects.filter(filters)

    def build_timeframe_filter(self, timeframe):
        try:
            # Year only: YYYY
            if re.match(r'^\d{4}$', timeframe):
                year = int(timeframe)
                return Q(date__year=year)
            
            # Year-Month: YYYY-MM
            elif re.match(r'^\d{4}-(?:0?[1-9]|1[0-2])$', timeframe):
                year, month = map(int, timeframe.split('-'))
                _, last_day = calendar.monthrange(year, month)
                start_date = datetime(year, month, 1).date()
                end_date = datetime(year, month, last_day).date()
                return Q(date__range=[start_date, end_date])
            
            # Year-Week: YYYY@WW
            elif re.match(r'^\d{4}@(?:[1-9]|0[1-9]|[1-4]\d|5[0-3])$', timeframe):
                year, week = map(int, timeframe.split('@'))
                # Pad week number to ensure it has two digits
                week_str = f"{week:02d}"
                start_date = datetime.strptime(f'{year}-W{week_str}-1', "%Y-W%W-%w").date()
                end_date = start_date + timedelta(days=6)
                return Q(date__range=[start_date, end_date])
            
            else:
                raise ValidationError({
                    "detail": "Invalid timeframe format. Use YYYY (e.g., 2025), YYYY-MM (e.g., 2025-01 or 2025-1), or YYYY@WW (e.g., 2025@01 or 2025@1)"
                })
                
        except ValueError as e:
            raise ValidationError({
                "detail": f"Invalid timeframe value: {str(e)}. Use YYYY (e.g., 2025), YYYY-MM (e.g., 2025-01 or 2025-1), or YYYY@WW (e.g., 2025@01 or 2025@1)"
            })

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_amount = Decimal('0.00')
        categories = defaultdict(lambda: {
            'total_amount': Decimal('0.00'),
            'record_count': 0,
            'subcategories': defaultdict(lambda: {
                'total_amount': Decimal('0.00'),
                'record_count': 0
            })
        })

        for record in queryset:
            category = record.category
            subcategory = record.subcategory
            amount = abs(record.amount)

            total_amount += amount
            categories[category]['total_amount'] += amount
            categories[category]['record_count'] += 1
            categories[category]['subcategories'][subcategory]['total_amount'] += amount
            categories[category]['subcategories'][subcategory]['record_count'] += 1

        color_cycle = cycle(colors)
        category_data = []
        details = {}

        for category, cat_data in categories.items():
            cat_total = cat_data['total_amount']
            cat_percentage = (cat_total / total_amount *
                              100).quantize(Decimal('0.01'))

            category_data.append({
                'value': float(cat_percentage),
                'color': next(color_cycle),
                'text': category
            })

            subcategories = []
            for subcategory, subcat_data in cat_data['subcategories'].items():
                subcat_total = subcat_data['total_amount']
                subcat_percentage = (
                    subcat_total / cat_total * 100).quantize(Decimal('0.01'))
                subcategories.append({
                    'subcategory': subcategory,
                    'total_amount': str(subcat_total),
                    'percentage': float(subcat_percentage),
                    'record_count': subcat_data['record_count']
                })

            subcategories.sort(key=lambda x: x['percentage'], reverse=True)

            details[category] = {
                'total_amount': str(cat_total),
                'record_count': cat_data['record_count'],
                'percentage': float(cat_percentage),
                'subcategories': subcategories
            }

        category_data.sort(key=lambda x: x['value'], reverse=True)

        result = {
            'total_amount': str(total_amount),
            'data': category_data,
            'details': details
        }

        return Response(result)
