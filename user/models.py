from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    account_status = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True,)
    nickname = models.CharField(
        max_length=100, null=True, blank=True, default="anonymous")

    def save(self, *args, **kwargs):
        # Check if there's an avatar and it has been updated
        if self.avatar:
            img = Image.open(self.avatar)
            if img.mode in ("RGBA", "P"):  # Convert image to RGB if necessary
                img = img.convert("RGB")

            # Compress the image
            output = BytesIO()
            # Adjust quality as needed
            img.save(output, format='JPEG', quality=70)
            output.seek(0)

            # Replace the ImageField with the compressed image
            self.avatar = ContentFile(output.read(), name=self.avatar.name)

        super().save(*args, **kwargs)
