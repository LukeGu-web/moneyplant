# Generated by Django 5.0.6 on 2024-08-03 01:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0008_alter_asset_group_alter_assetgroup_book'),
        ('record', '0006_remove_record_author_record_book_transfer_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='asset.asset'),
        ),
        migrations.AddField(
            model_name='transfer',
            name='from_asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='from_asset', to='asset.asset'),
        ),
        migrations.AddField(
            model_name='transfer',
            name='to_asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='to_asset', to='asset.asset'),
        ),
    ]