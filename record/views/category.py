from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from collections import defaultdict
from itertools import cycle
from record.models import Record
from book.models import Book


colors = ("#519DE9", "#7CC674", "#73C5C5", "#8481DD", "#F6D173", "#EF9234", "#A30000", "#D2D2D2",
          "#0066CC", "#4CB140", "#009596", "#5752D1", "#F4C145", "#EC7A08", "#7D1007", "#B8BBBE",
          "#004B95", "#38812F", "#005F60", "#3C3D99", "#F0AB00", "#C46100", "#470000", "#8A8D90",
          "#002F5D", "#23511E", "#003737", "#2A265F", "#C58C00", "#8F4700", "#2C0000", "#6A6E73",
          "#8BC1F7", "#BDE2B9", "#A2D9D9", "#B2B0EA", "#F9E0A2", "#F4B678", "#C9190B", "#F0F0F0")


class CategoriedRecordView(generics.ListAPIView):

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
        queryset = self.get_queryset()

        grouped_data = defaultdict(lambda: {
            'total_amount': Decimal('0.00'),
            'categories': defaultdict(lambda: {
                'total_amount': Decimal('0.00'),
                'record_count': 0,
                'subcategories': defaultdict(lambda: {
                    'total_amount': Decimal('0.00'),
                    'record_count': 0
                })
            })
        })

        for record in queryset:
            record_type = record.type
            category = record.category
            subcategory = record.subcategory
            amount = abs(record.amount)

            grouped_data[record_type]['total_amount'] += amount
            grouped_data[record_type]['categories'][category]['total_amount'] += amount
            grouped_data[record_type]['categories'][category]['record_count'] += 1
            grouped_data[record_type]['categories'][category]['subcategories'][subcategory]['total_amount'] += amount
            grouped_data[record_type]['categories'][category]['subcategories'][subcategory]['record_count'] += 1

        result = {}
        for record_type, type_data in grouped_data.items():
            type_total = type_data['total_amount']
            color_cycle = cycle(colors)
            category_data = []
            details = {}

            for category, cat_data in type_data['categories'].items():
                cat_total = cat_data['total_amount']
                cat_percentage = (cat_total / type_total *
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

                # Sort subcategories by percentage in descending order
                subcategories.sort(key=lambda x: x['percentage'], reverse=True)

                details[category] = {
                    'total_amount': str(cat_total),
                    'record_count': cat_data['record_count'],
                    'percentage': float(cat_percentage),
                    'subcategories': subcategories
                }

            # Sort category_data by value in descending order
            category_data.sort(key=lambda x: x['value'], reverse=True)

            result[record_type] = {
                'total_amount': str(type_total),
                'data': category_data,
                'details': details
            }

        return Response(result)
