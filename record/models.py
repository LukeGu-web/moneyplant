from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from book.models import Book
from asset.models import Asset

TYPE_CHOICES = (('income', 'income'), ('expense', 'expense'))


class Record(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True)
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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.type == 'expense' and self.amount > 0:
                self.amount = -self.amount  # Ensure amount is negative for expense

            if not self.pk:  # If the record is being created
                self._update_asset_balance(self.amount)
            else:  # If the record is being updated
                old_record = Record.objects.select_for_update().get(pk=self.pk)
                old_amount = old_record.amount
                self._update_asset_balance(self.amount - old_amount)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self._update_asset_balance(-self.amount)
            super().delete(*args, **kwargs)

    def _update_asset_balance(self, amount_change):
        if self.asset:
            self.asset = Asset.objects.select_for_update().get(pk=self.asset.pk)
            self.asset.balance = self.asset.balance + \
                Decimal(str(amount_change))
            self.asset.save()


class Transfer(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True)
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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.pk:  # If the transfer is being created
                self._update_asset_balances(self.amount)
            else:  # If the transfer is being updated
                old_transfer = Transfer.objects.select_for_update().get(pk=self.pk)
                old_amount = old_transfer.amount
                self._update_asset_balances(self.amount - old_amount)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self._update_asset_balances(-self.amount)
            super().delete(*args, **kwargs)

    def _update_asset_balances(self, amount_change):
        if self.from_asset:
            self.from_asset = Asset.objects.select_for_update().get(pk=self.from_asset.pk)
            self.from_asset.balance -= Decimal(str(amount_change))
            self.from_asset.save()
        if self.to_asset:
            self.to_asset = Asset.objects.select_for_update().get(pk=self.to_asset.pk)
            self.to_asset.balance += Decimal(str(amount_change))
            self.to_asset.save()
