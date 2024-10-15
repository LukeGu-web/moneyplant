from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ValidationError
from django.conf import settings
from django.core.files.base import ContentFile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    account_status = models.CharField(max_length=20, default="unverified")
    expo_push_token = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.BinaryField(null=True, blank=True)
    nickname = models.CharField(
        max_length=100, null=True, blank=True, default="anonymous")
