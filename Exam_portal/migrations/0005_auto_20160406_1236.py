# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-06 12:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Exam_portal', '0004_auto_20160330_1153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentanswer',
            name='answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Exam_portal.QuestionChoice'),
        ),
    ]
