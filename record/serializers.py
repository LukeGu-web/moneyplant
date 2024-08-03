from rest_framework import serializers
from .models import Record, Transfer


class RecordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    book = serializers.CharField()
    asset = serializers.CharField()

    class Meta:
        model = Record
        fields = "__all__"


class TransferSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    book = serializers.CharField()
    asset = serializers.CharField()

    class Meta:
        model = Transfer
        fields = "__all__"
