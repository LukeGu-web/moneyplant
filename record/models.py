from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.

TYPE_CHOICES = (('income', 'income'), ('expense', 'expense'))


class Record(models.Model):
    # book=models.ForeignKey(User, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='expense'
    )
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200, blank=True, default='')
    note = models.CharField(max_length=500, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transfer(models.Model):
    # book=models.ForeignKey(User, on_delete=models.CASCADE)
    # from_asset=models.ForeignKey(User, on_delete=models.CASCADE)
    # to_asset=models.ForeignKey(User, on_delete=models.CASCADE)

    note = models.CharField(max_length=500, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
