from django.contrib.auth.models import User
from rest_framework import serializers


def required(value):
    if value is None:
        raise serializers.ValidationError('This field is required')


class DeviceRegisterSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(validators=[required])

    class Meta:
        model = User
        fields = ['username', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserRegisterSerializer(DeviceRegisterSerializer):
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta(DeviceRegisterSerializer.Meta):
        model = User
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
