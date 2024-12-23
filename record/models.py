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
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateTimeField()
    next_occurrence = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active')
    last_run = models.DateTimeField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    # For weekly schedules
    week_days = models.JSONField(
        default=list, blank=True, help_text="List of weekdays (0-6) for weekly schedules, where Monday is 0 and Sunday is 6")

    # For monthly schedules
    month_day = models.IntegerField(
        null=True, blank=True, help_text="Day of month for monthly schedules")

    class Meta:
        db_table = 'scheduled_record'
        indexes = [
            models.Index(fields=['status', 'next_occurrence']),
            models.Index(fields=['frequency']),
        ]

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new:
            self.next_occurrence = self._calculate_next_occurrence(
                self.start_date)

        super().save(*args, **kwargs)

        # Create or update the periodic task
        from .tasks import create_or_update_periodic_task
        create_or_update_periodic_task(self)

    def delete(self, *args, **kwargs):
        # Clean up associated periodic task
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(name=f"process_record_{self.id}").delete()
        super().delete(*args, **kwargs)

    def _calculate_next_occurrence(self, current_datetime):
        """Calculate the next occurrence based on the frequency."""
        if not self.status == 'active':
            return current_datetime

        if self.end_date and current_datetime >= self.end_date:
            self.status = 'completed'
            return current_datetime

        if self.frequency == 'daily':
            next_date = current_datetime + timedelta(days=1)

        elif self.frequency == 'weekly':
            if self.week_days:
                # Find the next allowed weekday
                next_date = current_datetime + timedelta(days=1)
                while next_date.weekday() not in self.week_days:
                    next_date += timedelta(days=1)
            else:
                next_date = current_datetime + timedelta(weeks=1)

        elif self.frequency == 'monthly':
            if self.month_day:
                if not 1 <= self.month_day <= 31:
                    raise ValueError("month_day must be between 1 and 31")
                
                # Try to set the day in current month
                current_month_target = current_datetime.replace(day=1)  # Go to first of month to avoid invalid dates
                current_month_target = current_month_target.replace(day=min(self.month_day,
                    (current_month_target + relativedelta(months=1, days=-1)).day))
                
                # If we haven't passed this day yet in current month, use it
                if current_month_target > current_datetime:
                    next_date = current_month_target
                else:
                    # Otherwise, go to next month
                    next_date = (current_datetime + relativedelta(months=1)).replace(day=1)  # First go to 1st
                    next_date = next_date.replace(day=min(self.month_day,
                        (next_date + relativedelta(months=1, days=-1)).day))
            else:
                next_date = current_datetime + relativedelta(months=1)

        elif self.frequency == 'annually':
            next_date = current_datetime + relativedelta(years=1)

        else:
            return current_datetime

        # If next occurrence is past end_date, mark as completed
        if self.end_date and next_date > self.end_date:
            self.status = 'completed'
            return current_datetime

        return next_date

    def update_next_occurrence(self):
        """Update the next occurrence after a task has run."""
        self.last_run = timezone.now()
        self.next_occurrence = self._calculate_next_occurrence(
            self.next_occurrence)
        self.save()

    def pause(self):
        """Pause the scheduled record."""
        self.status = 'paused'
        self.save()

    def resume(self):
        """Resume the scheduled record."""
        self.status = 'active'
        self.next_occurrence = self._calculate_next_occurrence(timezone.now())
        self.save()

    def has_conflicts(self):
        """Check for conflicting schedules."""
        return ScheduledRecord.objects.filter(
            book=self.book,
            status='active',
            next_occurrence=self.next_occurrence
        ).exclude(pk=self.pk).exists()

    @property
    def is_due(self):
        """Check if the task is due for execution."""
        return (
            self.status == 'active' and
            self.next_occurrence <= timezone.now() and
            (not self.end_date or self.next_occurrence <= self.end_date)
        )
