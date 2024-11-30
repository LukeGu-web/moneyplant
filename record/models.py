from django.db import models, transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta
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
            # Ensure date is timezone-aware
            if self.date and timezone.is_naive(self.date):
                self.date = timezone.make_aware(
                    self.date, timezone.get_current_timezone())

            if self.type == 'expense' and self.amount > 0:
                self.amount = -self.amount  # Ensure amount is negative for expense

            if not self.pk:  # If the record is being created
                self._update_asset_balance(self.amount)
            else:  # If the record is being updated
                old_record = Record.objects.select_for_update().get(pk=self.pk)
                old_amount = old_record.amount
                old_asset = old_record.asset

                # Handle the case when an asset is assigned for the first time
                if not old_asset and self.asset:
                    self._update_asset_balance(self.amount)
                elif old_asset != self.asset:
                    # If the asset has changed, update both old and new assets
                    if old_asset:
                        self._update_asset_balance(-old_amount, old_asset)
                    if self.asset:
                        self._update_asset_balance(self.amount)
                else:
                    # If the asset hasn't changed, update with the difference
                    self._update_asset_balance(self.amount - old_amount)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self._update_asset_balance(-self.amount)
            super().delete(*args, **kwargs)

    def _update_asset_balance(self, amount_change, asset=None):
        asset_to_update = asset or self.asset
        if asset_to_update:
            asset_to_update = Asset.objects.select_for_update().get(pk=asset_to_update.pk)
            asset_to_update.balance += Decimal(str(amount_change))
            asset_to_update.save()


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
            # Ensure date is timezone-aware
            if self.date and timezone.is_naive(self.date):
                self.date = timezone.make_aware(
                    self.date, timezone.get_current_timezone())
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


class ScheduledRecord(Record):
    FREQUENCY_CHOICES = [
        ('daily', 'daily'),
        ('weekly', 'weekly'),
        ('monthly', 'monthly'),
        ('annually', 'annually'),
    ]

    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateTimeField()  # Includes both date and time
    next_occurrence = models.DateTimeField()

    class Meta:
        db_table = 'scheduled_record'

    def save(self, *args, **kwargs):
        if not self.pk:  # New scheduled record
            self.next_occurrence = self._calculate_next_occurrence(
                self.start_date)
        super().save(*args, **kwargs)

    def _calculate_next_occurrence(self, current_datetime):
        """Calculate the next occurrence based on the frequency."""
        if self.frequency == 'daily':
            return current_datetime + timedelta(days=1)
        elif self.frequency == 'weekly':
            return current_datetime + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return current_datetime + relativedelta(months=1)
        elif self.frequency == 'annually':
            return current_datetime + relativedelta(years=1)
        return current_datetime
