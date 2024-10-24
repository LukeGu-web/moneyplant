# Generated by Django 5.1 on 2024-10-23 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_account_expo_push_token_alter_account_account_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='auth_provider',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='social_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]