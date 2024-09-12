from rest_framework import serializers
from .models import Book
from asset.serializers import AssetGroupSerializer
from asset.models import AssetGroup


class BookSerializer(serializers.ModelSerializer):
    # response includes groups
    groups = AssetGroupSerializer(many=True, required=False)

    class Meta:
        model = Book
        exclude = ['user']

    def create(self, validated_data):
        # Extract AssetGroup data from the validated data
        groups_data = validated_data.pop('groups', [])

        # Create the Book instance
        book = Book.objects.create(**validated_data)

        # Create AssetGroups and associate them with the Book
        for group_data in groups_data:
            AssetGroup.objects.create(book=book, **group_data)

        return book

    def to_representation(self, instance):
        # Get the original representation
        representation = super().to_representation(instance)

        # If the request method is GET and it's for the list view, remove 'groups'
        request = self.context.get('request')
        if request and request.method == 'GET' and 'pk' not in request.parser_context['kwargs']:
            representation.pop('groups', None)

        return representation
