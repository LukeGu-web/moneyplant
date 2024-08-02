from rest_framework import serializers
from .models import Asset, AssetGroup


def bill_day_valid(value):
    if value < 1 or value > 29:
        raise serializers.ValidationError("value should between 1 and 29")
    else:
        return value


class AssetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    bill_day = serializers.IntegerField(validators=[bill_day_valid])
    repayment_day = serializers.IntegerField(validators=[bill_day_valid])

    class Meta:
        model = Asset
        fields = "__all__"


class AssetGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    group = AssetSerializer(many=True, read_only=True)

    class Meta:
        model = AssetGroup
        fields = "__all__"
