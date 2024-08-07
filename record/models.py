from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from book.models import Book
from asset.models import Asset
# Create your models here.

TYPE_CHOICES = (('income', 'income'), ('expense', 'expense'))


class Record(models.Model):
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    asset = models.ForeignKey(
        Asset, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='expense'
    )
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200, blank=True, default='')
    is_marked_tax_return = models.BooleanField(blank=True, default=False)
    note = models.CharField(max_length=500, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transfer(models.Model):
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    from_asset = models.ForeignKey(
        Asset, on_delete=models.SET_NULL, null=True, related_name='from_asset')
    to_asset = models.ForeignKey(
        Asset, on_delete=models.SET_NULL, null=True, related_name='to_asset')
    type = models.CharField(default='transfer')
    note = models.CharField(max_length=500, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
