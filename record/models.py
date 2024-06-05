from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Record(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=200)
    note = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
