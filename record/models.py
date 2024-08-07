from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from book.models import Book
from asset.models import Asset
# Create your models here.

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
        if not self.pk:  # If the record is being created
            if self.asset:
                self.asset.balance -= self.amount
                self.asset.save()
        else:  # If the record is being updated
            old_record = Record.objects.get(pk=self.pk)
            if old_record.asset and old_record.asset != self.asset:
                old_record.asset.balance += old_record.amount
                old_record.asset.save()
                if self.asset:
                    self.asset.balance -= self.amount
                    self.asset.save()
            elif self.asset:
                balance_change = self.amount - old_record.amount
                self.asset.balance -= balance_change
                self.asset.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.asset:
            self.asset.balance += self.amount
            self.asset.save()
        super().delete(*args, **kwargs)


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
        if not self.pk:  # If the transfer is being created
            if self.from_asset:
                self.from_asset.balance -= self.amount
                self.from_asset.save()
            if self.to_asset:
                self.to_asset.balance += self.amount
                self.to_asset.save()
        else:  # If the transfer is being updated
            old_transfer = Transfer.objects.get(pk=self.pk)
            if old_transfer.from_asset:
                old_transfer.from_asset.balance += old_transfer.amount
                old_transfer.from_asset.save()
            if old_transfer.to_asset:
                old_transfer.to_asset.balance -= old_transfer.amount
                old_transfer.to_asset.save()

            if self.from_asset:
                self.from_asset.balance -= self.amount
                self.from_asset.save()
            if self.to_asset:
                self.to_asset.balance += self.amount
                self.to_asset.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.from_asset:
            self.from_asset.balance += self.amount
            self.from_asset.save()
        if self.to_asset:
            self.to_asset.balance -= self.amount
            self.to_asset.save()
        super().delete(*args, **kwargs)
