from rest_framework import serializers
from .models import Record, Transfer
from decimal import Decimal


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = ['id', 'type', 'category', 'subcategory',
                  'is_marked_tax_return', 'note', 'amount', 'date', 'book', 'asset']


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['id', 'type', 'note', 'amount',
                  'date', 'book', 'from_asset', 'to_asset']


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


class SubcategoryGroupSerializer(serializers.Serializer):
    subcategory = serializers.CharField()
    records = RecordSerializer(many=True)


class CategoryGroupSerializer(serializers.Serializer):
    category = serializers.CharField()
    subcategories = SubcategoryGroupSerializer(many=True)


class GroupedRecordSerializer(serializers.Serializer):
    type = serializers.CharField()
    categories = CategoryGroupSerializer(many=True)
