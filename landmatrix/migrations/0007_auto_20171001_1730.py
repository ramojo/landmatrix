# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-10-01 15:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('landmatrix', '0006_auto_20170928_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalactivity',
            name='public_version',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historical_version', to='landmatrix.Activity'),
        ),
    ]
