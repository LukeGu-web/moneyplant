# Generated by Django 5.0.6 on 2024-08-01 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0004_remove_asset_bill_day_remove_asset_repayment_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='bill_day',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='repayment_day',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]