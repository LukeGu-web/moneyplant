# Generated by Django 5.1 on 2024-09-02 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_account_account_id_account_avatar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='avatar',
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
