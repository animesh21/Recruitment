# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-10 07:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Exam_portal', '0004_auto_20160709_1130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='warn_time',
            field=models.IntegerField(),
        ),
    ]