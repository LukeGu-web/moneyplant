from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    note = models.CharField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.name
