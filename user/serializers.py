from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from rest_framework import serializers
from io import BytesIO
import base64
from PIL import Image
from .models import Account


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Check if the input is a base64 string
        if isinstance(data, str) and data.startswith('data:image'):
            # Get the file format (jpg, png, etc.) and the base64 data
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]  # Get the file extension

            # Decode the base64 data
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)

    def to_representation(self, value):
        # Convert the file to a base64 string for serialization
        if value:
            # Since 'value' is a bytes object, no need to call 'read'
            binary_data = value  # Already bytes

            # Encode the binary data to base64
            base64_data = base64.b64encode(binary_data).decode('utf-8')

            # Determine the file's MIME type and format accordingly
            file_ext = 'jpg'  # Assuming the image is stored as JPG
            mime_type = f"image/{file_ext}"

            # Return the base64 string in the appropriate format
            return f"data:{mime_type};base64,{base64_data}"

        return None


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
    account_id = serializers.CharField(allow_null=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    nickname = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        avatar = validated_data.pop('avatar', None)

        # Create User instance
        user = User.objects.create_user(**user_data)

        # Handle image conversion to binary
        if avatar:
            validated_data['avatar'] = avatar.read()

        # Create Account instance
        account = Account.objects.create(user=user, **validated_data)
        return account

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        avatar = validated_data.pop('avatar', None)

        # Update user instance
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Handle image conversion to binary
        if avatar:
            instance.avatar = avatar.read()

        # Update the rest of the Account instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def compress_image(self, image):
        max_size = 5 * 1024 * 1024  # 5MB

        # Compress the image
        img = Image.open(image)
        if img.mode in ("RGBA", "P"):  # Convert to RGB if necessary
            img = img.convert("RGB")

        output = BytesIO()
        img.save(output, format='JPEG', quality=70, optimize=True)
        output.seek(0)

        # Check the size of the compressed image
        if output.tell() > max_size:
            raise serializers.ValidationError(
                "The avatar image size must be less than 5MB.")

        return output.read()
