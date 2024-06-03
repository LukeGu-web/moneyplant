from django.db import models

# Create your models here.


class User(models.Model):
    account = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    userStatus = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phoneNumber = models.CharField(max_length=200)
