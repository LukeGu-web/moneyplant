# Generated by Django 5.0.6 on 2024-06-26 00:24

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0003_record_created_at_record_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
