# Generated by Django 5.0.6 on 2024-06-05 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('record', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='type',
            field=models.CharField(choices=[('income', 'income'), ('expense', 'expense')], default='expense', max_length=10),
        ),
    ]
