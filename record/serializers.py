from rest_framework import serializers
from .models import Record


class RecordSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Record
        fields = "__all__"
