# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-02 18:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0041_jobtypetag'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='jobtypetag',
            table='job_type_tag',
        ),
    ]
