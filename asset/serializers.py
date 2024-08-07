from rest_framework import serializers
from .models import Asset, AssetGroup


def bill_day_valid(value):
    if value < 1 or value > 29:
        raise serializers.ValidationError("value should between 1 and 29")
    else:
        return value


class AssetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    bill_day = serializers.IntegerField(
        required=False, allow_null=True, validators=[bill_day_valid])
    repayment_day = serializers.IntegerField(
        required=False, allow_null=True, validators=[bill_day_valid])

    class Meta:
        model = Asset
        fields = "__all__"


class AssetGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    assets = AssetSerializer(many=True, read_only=True)

    class Meta:
        model = AssetGroup
        fields = "__all__"
