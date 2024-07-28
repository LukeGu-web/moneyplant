from django.db import models


class Asset(models.Model):
    # book=models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    group_name = models.CharField(max_length=200, blank=True, default='')
    is_credit = models.BooleanField(blank=True, default=False)
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, default=0)
    bill_day = models.DateTimeField(blank=True)
    repayment_day = models.DateTimeField(blank=True)
    is_total_asset = models.BooleanField(blank=True, default=True)
    is_no_budget = models.BooleanField(blank=True, default=False)
    note = models.CharField(max_length=500, blank=True, default='')
