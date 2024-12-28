# Generated by Django 5.1 on 2024-12-28 01:39

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0011_scheduledrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledrecord',
            name='num_of_days',
            field=models.PositiveIntegerField(default=1, help_text='Number of days between occurrences for daily schedules (1-365)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(365)]),
        ),
        migrations.AlterField(
            model_name='scheduledrecord',
            name='week_days',
            field=models.JSONField(blank=True, default=list, help_text='List of weekdays (0-6) for weekly schedules, where Monday is 0 and Sunday is 6'),
        ),
    ]
