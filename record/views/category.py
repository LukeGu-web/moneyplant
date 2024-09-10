from rest_framework import generics
from rest_framework.response import Response
from record.models import Record
from record.utils import string_to_color
from decimal import Decimal
from collections import defaultdict


class CategoriedRecordView(generics.ListAPIView):
    queryset = Record.objects.all()

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
            category_data = []
            details = {}

            for category, cat_data in type_data['categories'].items():
                cat_total = cat_data['total_amount']
                cat_percentage = (cat_total / type_total *
                                  100).quantize(Decimal('0.1'))

                category_data.append({
                    'value': int(cat_percentage),
                    'color': string_to_color(category),
                    'text': category
                })

                subcategories = []
                for subcategory, subcat_data in cat_data['subcategories'].items():
                    subcat_total = subcat_data['total_amount']
                    subcat_percentage = (
                        subcat_total / cat_total * 100).quantize(Decimal('0.1'))
                    subcategories.append({
                        'subcategory': subcategory,
                        'total_amount': str(subcat_total),
                        'percentage': float(subcat_percentage),
                        'record_count': subcat_data['record_count']
                    })

                details[category] = {
                    'total_amount': str(cat_total),
                    'record_count': cat_data['record_count'],
                    'percentage': float(cat_percentage),
                    'subcategories': subcategories
                }

            result[record_type] = {
                'total_amount': str(type_total),
                'data': category_data,
                'details': details
            }

        return Response(result)
