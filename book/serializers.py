from rest_framework import serializers
from .models import Book
from asset.serializers import AssetGroupSerializer


class BookSerializer(serializers.ModelSerializer):
    # user = serializers.StringRelatedField(read_only=True)
    book = AssetGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        exclude = ['id', 'user']
