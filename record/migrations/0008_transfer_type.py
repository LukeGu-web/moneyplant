# Generated by Django 5.0.6 on 2024-08-03 03:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0007_record_asset_transfer_from_asset_transfer_to_asset'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='type',
            field=models.CharField(default='transfer'),
        ),
    ]
