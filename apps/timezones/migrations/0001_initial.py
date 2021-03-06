# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-15 19:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Timezone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=200)),
                ('offset_hours', models.IntegerField()),
                ('offset_minutes', models.IntegerField()),
                ('country_code', models.CharField(max_length=3)),
                ('country_name', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ('offset_hours', 'offset_minutes', 'name'),
            },
        ),
    ]
