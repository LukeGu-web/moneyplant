from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Account


# def required(value):
#     if value is None:
#         raise serializers.ValidationError('This field is required')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
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


class DeviceRegisterSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Account
        fields = ['id', 'user', 'accountStatus']

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


class UserRegisterSerializer(DeviceRegisterSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta(DeviceRegisterSerializer.Meta):
        model = Account
        fields = DeviceRegisterSerializer.Meta.fields + ['password2']

    def save(self):
        password = self.validated_data['password']
        password2 = self.validated_data['password2']

        if password != password2:
            raise serializers.ValidationError(
                {"Error": "Password Does not match"})

        if User.objects.filter(email=self.validated_data['email']).exists():
            raise serializers.ValidationError({"Error": "Email already exist"})

        account = User(
            email=self.validated_data['email'], username=self.validated_data['username'])

        account = User(username=self.validated_data['username'])
        account.set_password(password)
        account.save()

        return account
