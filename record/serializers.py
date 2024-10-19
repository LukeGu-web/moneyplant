from rest_framework import serializers
from django.utils import timezone
from .models import Record, Transfer


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ['id', 'type', 'category', 'subcategory',
                  'is_marked_tax_return', 'note', 'amount', 'date', 'book', 'asset']

    def validate_date(self, value):
        # Ensure the date is timezone-aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['id', 'type', 'note', 'amount',
                  'date', 'book', 'from_asset', 'to_asset']

    def validate_date(self, value):
        # Ensure the date is timezone-aware
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value


class CombinedRecordSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Record):
            return RecordSerializer(instance).data
        elif isinstance(instance, Transfer):
            data = TransferSerializer(instance).data
            data['type'] = 'transfer'
            return data


class GroupedDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    records = CombinedRecordSerializer(many=True)
    sum_of_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    sum_of_expense = serializers.DecimalField(max_digits=12, decimal_places=2)


class MonthlyDataSerializer(serializers.Serializer):
    month = serializers.DateTimeField(format="%Y-%m")
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
