from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Account


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    account_id = serializers.CharField(read_only=True, allow_null=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    created_date = serializers.DateTimeField(read_only=True)
    nickname = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data['user']
        new_user = UserSerializer.create(
            UserSerializer(), validated_data=user_data)
        account, created = Account.objects.update_or_create(
            user=new_user,
            defaults={**validated_data}
        )
        result = {
            "id": account.id,
            "account_status": account.account_status,
            "avatar": account.avatar,
            "nickname": account.nickname,
            "created_at": account.created_at,
            "account_id": account.account_id
        }
        return result

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = self.fields['user']
            user_instance = instance.user
            user_serializer.update(user_instance, user_data)

        # Update Account fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
