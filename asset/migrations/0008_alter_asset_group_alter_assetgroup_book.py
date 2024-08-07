# Generated by Django 5.0.6 on 2024-08-03 00:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0007_assetgroup_book'),
        ('book', '0002_alter_book_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets', to='asset.assetgroup'),
        ),
        migrations.AlterField(
            model_name='assetgroup',
            name='book',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups', to='book.book'),
        ),
    ]
