from rest_framework import serializers
from .models import Asset, AssetGroup


class AssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Asset
        fields = "__all__"


class AssetGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AssetGroup
        fields = "__all__"
