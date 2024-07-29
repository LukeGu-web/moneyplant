from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    note = models.CharField(max_length=500, blank=True, default='')