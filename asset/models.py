from django.db import models
from book.models import Book


class AssetGroup(models.Model):
    name = models.CharField(max_length=100)
    book = models.ForeignKey(
        Book, on_delete=models.SET_NULL, null=True, related_name='book')

    def __str__(self):
        return self.name


class Asset(models.Model):
    name = models.CharField(max_length=200, default='')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    group = models.ForeignKey(
        AssetGroup, on_delete=models.SET_NULL, null=True, related_name='group')
    is_credit = models.BooleanField(blank=True, default=False)
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, default=0)
    bill_day = models.IntegerField(blank=True, null=True)
    repayment_day = models.IntegerField(blank=True, null=True)
    is_total_asset = models.BooleanField(blank=True, default=True)
    is_no_budget = models.BooleanField(blank=True, default=False)
    note = models.CharField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.name
