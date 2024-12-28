from rest_framework import serializers
from django.utils import timezone
from .models import Record, Transfer, ScheduledRecord
from book.models import Book
from asset.models import Asset


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

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError("Amount cannot be zero")
        return value

    def validate(self, data):
        if data.get('type') == 'expense' and data.get('amount', 0) > 0:
            data['amount'] = -abs(data['amount'])
        return data


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

    def validate(self, data):
        if data.get('from_asset') == data.get('to_asset'):
            raise serializers.ValidationError(
                "Transfer must be between different assets"
            )
        if data.get('amount', 0) <= 0:
            raise serializers.ValidationError(
                "Transfer amount must be positive"
            )
        return data


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


class ScheduledRecordSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        required=True
    )
    asset = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = ScheduledRecord
        fields = [
            # Record fields
            'id', 'book', 'asset', 'type', 'category', 'subcategory',
            'is_marked_tax_return', 'note', 'amount', 'date',
            # ScheduledRecord fields
            'frequency', 'start_date', 'end_date', 'status', 'next_occurrence',
            'last_run', 'num_of_days', 'week_days', 'month_day'
        ]
        read_only_fields = ['next_occurrence', 'last_run']

    def validate(self, data):
        """
        Custom validation for schedule-specific fields.
        """
        if data.get('frequency') != 'daily' and data.get('num_of_days', 1) != 1:
            raise serializers.ValidationError(
                {'num_of_days': 'Number of days can only be set for daily frequency'}
            )

        if data.get('frequency') == 'weekly' and not data.get('week_days'):
            raise serializers.ValidationError(
                {'week_days': 'Week days must be specified for weekly frequency'}
            )

        if data.get('frequency') == 'monthly' and not data.get('month_day'):
            raise serializers.ValidationError(
                {'month_day': 'Month day must be specified for monthly frequency'}
            )

        if 'end_date' in data and data['end_date'] and data['end_date'] < data['start_date']:
            raise serializers.ValidationError(
                {'end_date': 'End date must be after start date'}
            )

        return data

    def validate_num_of_days(self, value):
        if not 1 <= value <= 365:
            raise serializers.ValidationError(
                'Number of days must be between 1 and 365'
            )
        return value

    def validate_week_days(self, value):
        if value and not all(isinstance(day, int) and 0 <= day <= 6 for day in value):
            raise serializers.ValidationError(
                'Week days must be integers between 0 and 6'
            )
        return value

    def validate_month_day(self, value):
        if value and not (1 <= value <= 31):
            raise serializers.ValidationError(
                'Month day must be between 1 and 31'
            )
        return value

    def validate_start_date(self, value):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def validate_end_date(self, value):
        if value and timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value
