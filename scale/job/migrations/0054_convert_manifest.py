# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-12 11:53
from __future__ import unicode_literals

from django.db import migrations

from job.deprecation import JobInterfaceSunset
from job.seed.manifest import SeedManifest

def convert_interface_to_manifest(apps, schema_editor):
    # Go through all of the JobType models and convert legacy interfaces to Seed manifests
    # Also inactivate/pause them
    JobType = apps.get_model('job', 'JobType')

    unique = 0
    for jt in JobType.objects.all().iterator():
        if JobInterfaceSunset.is_seed_dict(jt.manifest):
            continue
        jt.is_active = False
        jt.is_paused = True
        old_name_version = jt.name + ' ' + jt.version
        jt.name = 'legacy-' + jt.name.replace('_', '-')
        jt.version = '1.0.%d' % unique
        unique += 1
        if not jt.manifest:
            jt.manifest = {}
            
        input_files = []
        input_json = []
        output_files = []
        unique_name = 0
        for input in jt.manifest.get('input_data', []):
            type = input.get('type', '')
            if 'file' not in type:
                json = {}
                json['name'] = input.get('name') + str(unique_name)
                unique_name += 1
                json['type'] = 'string'
                json['required'] = input.get('required', True)
                input_json.append(json)
                continue
            file = {}
            file['name'] = input.get('name') + str(unique_name)
            unique_name += 1
            file['required'] = input.get('required', True)
            file['partial'] = input.get('partial', False)
            file['mediaTypes'] = input.get('media_types', [])
            file['multiple'] = (type == 'files')
            input_files.append(file)
            
        for output in jt.manifest.get('output_data', []):
            type = output.get('type', '')
            file = {}
            file['name'] = output.get('name') + str(unique_name)
            unique_name += 1
            file['required'] = output.get('required', True)
            file['mediaType'] = output.get('media_type', [])
            file['multiple'] = (type == 'files')
            file['pattern'] = "*.*"
            output_files.append(file)
            
        mounts = []
        for mount in jt.manifest.get('mounts', []):
            mt = {}
            mt['name'] = mount.get('name') + str(unique_name)
            unique_name += 1
            mt['path'] = mount.get('path')
            mt['mode'] = mount.get('mode', 'ro')
            mounts.append(mt)
            
        settings = []
        for setting in jt.manifest.get('settings', []):
            s = {}
            s['name'] = setting.get('name') + str(unique_name)
            unique_name += 1
            s['secret'] = setting.get('secret', False)
            settings.append(s)
        for var in jt.manifest.get('env_vars', []):
            s = {}
            s['name'] = 'ENV_' + setting.get('name') + str(unique_name)
            unique_name += 1
            settings.append(s)
        
        errors = []
        ec = jt.error_mapping.get('exit_codes', {})
        for exit_code, error_name in ec.items():
            error = {
                'code': int(exit_code),
                'name': error_name,
                'title': 'Error Name',
                'description': 'Error Description',
                'category': 'algorithm'
            }
            errors.append(error)
            
        new_manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': jt.name,
                'jobVersion': jt.version,
                'packageVersion': '1.0.0',
                'title': 'LEGACY ' + jt.title,
                'description': jt.description,
                'tags': [jt.category, old_name_version],
                'maintainer': {
                  'name': jt.author_name,
                  'email': 'jdoe@example.com',
                  'url': jt.author_url
                },
                'timeout': jt.timeout,
                'interface': {
                  'command': jt.manifest.get('command', ''),
                  'inputs': {
                    'files': input_files,
                    'json': input_json
                  },
                  'outputs': {
                    'files': output_files,
                    'json': []
                  },
                  'mounts': mounts,
                  'settings': settings
                },
                'resources': {
                  'scalar': [
                    { 'name': 'cpus', 'value': jt.cpus_required },
                    { 'name': 'mem', 'value': jt.mem_const_required, 'inputMultiplier': jt.mem_mult_required },
                    { 'name': 'sharedMem', 'value': jt.shared_mem_required },
                    { 'name': 'disk', 'value': jt.disk_out_const_required, 'inputMultiplier': jt.disk_out_mult_required }
                  ]
                },
                'errors': errors
              }
            }
        jt.manifest = new_manifest
        SeedManifest(jt.manifest, do_validate=True)
        jt.save()

class Migration(migrations.Migration):

    dependencies = [
        ('job', '0053_jobtype_unmet_resources'),
    ]

    operations = [
        migrations.RunPython(convert_interface_to_manifest),
    ]
