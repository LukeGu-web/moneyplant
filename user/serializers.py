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

    class Meta:
        model = Account
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data['user']
        new_user = UserSerializer.create(
            UserSerializer(), validated_data=user_data)
        account, created = Account.objects.update_or_create(
            user=new_user,
            accountStatus=validated_data['accountStatus']
        )
        result = {"id": account.id, 'accountStatus': account.accountStatus}
        return result

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = self.fields['user']
        user_instance = instance.user
        account_updated = super().update(instance, validated_data)
        if user_data:
            meta = user_serializer.update(
                instance=user_instance, validated_data=user_data)
            account_updated.meta = meta
        # accountStatus = self.fields['accountStatus']
        # if accountStatus == "unregistered":
        # if User.objects.filter(email=self.validated_data['email']).exists():
        #     raise serializers.ValidationError({"Error": "Email already exist"})
        return account_updated
