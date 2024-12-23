# Generated by Django 5.1 on 2024-12-21 03:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0010_alter_record_book_alter_transfer_book_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledRecord',
            fields=[
                ('record_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='record.record')),
                ('frequency', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('annually', 'Annually')], max_length=10)),
                ('start_date', models.DateTimeField()),
                ('next_occurrence', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed')], default='active', max_length=10)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('celery_task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('week_days', models.JSONField(blank=True, default=list, help_text='List of weekdays (0-6) for weekly schedules')),
                ('month_day', models.IntegerField(blank=True, help_text='Day of month for monthly schedules', null=True)),
            ],
            options={
                'db_table': 'scheduled_record',
                'indexes': [models.Index(fields=['status', 'next_occurrence'], name='scheduled_r_status_10097e_idx'), models.Index(fields=['frequency'], name='scheduled_r_frequen_abc3fd_idx')],
            },
            bases=('record.record',),
        ),
    ]
