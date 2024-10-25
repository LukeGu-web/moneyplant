from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)


class Account(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='account'
    )
    account_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    account_status = models.CharField(max_length=20, default="unverified")
    expo_push_token = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.BinaryField(null=True, blank=True)
    nickname = models.CharField(
        max_length=100, null=True, blank=True, default="anonymous")
    auth_provider = models.CharField(max_length=20, blank=True, null=True)
    social_id = models.CharField(max_length=255, blank=True, null=True)

    def delete(self, *args, **kwargs):
        """
        Override delete method to ensure proper deletion of user
        """
        try:
            with transaction.atomic():
                # Store reference to user
                user = self.user

                # Delete token if exists
                Token.objects.filter(user=user).delete()

                # Clear social auth data if exists
                if self.auth_provider:
                    self.auth_provider = None
                    self.social_id = None
                    self.save(update_fields=['auth_provider', 'social_id'])

                # Delete the account first
                super().delete(*args, **kwargs)

                # Delete the user last
                user.delete()

                logger.info(f"Successfully deleted account {
                            self.id} and associated user {user.id}")

        except Exception as e:
            logger.error(f"Error during account deletion: {str(e)}")
            raise

    class Meta:
        db_table = 'user_account'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create auth token for new users"""
    if created:
        Token.objects.create(user=instance)
