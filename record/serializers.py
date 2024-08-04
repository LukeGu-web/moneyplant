from rest_framework import serializers
from .models import Record, Transfer


class RecordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    book = serializers.CharField()
    asset = serializers.CharField()

    class Meta:
        model = Record
        exclude = ['created_at', 'updated_at']


class TransferSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    book = serializers.CharField()
    from_asset = serializers.CharField()
    to_asset = serializers.CharField()

    class Meta:
        model = Transfer
        exclude = ['created_at', 'updated_at']
