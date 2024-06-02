from django.db import models

# Create your models here.


class Record(models.Model):
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200)
    note = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
