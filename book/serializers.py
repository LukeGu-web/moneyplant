from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = "__all__"
