# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-09 20:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0049_auto_20180927_1531'),
    ]
    
    def update_job_inputs(apps, schemaEditor):
        Job = apps.get_model('job', 'Job')
        
        for job in Job.objects.all().iterator():
            job_input = job.input
            if job_input and 'files' in job_input:
                if 'input_file' in job_input['files'] and isinstance(job_input['files']['input_file'], list):
                    input_file = {}
                    input_file['file_ids'] = job_input['files']['input_file']
                    input_file['multiple'] = len(job_input['files']['input_file'] > 1)
                    job_input['files']['input_file'] = input_file
                    job.save()

    operations = [
        migrations.RunPython(update_job_inputs),
    ]