# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-18 06:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('val', models.CharField(max_length=128, unique=True)),
                ('expire', models.IntegerField(default=300, verbose_name='超时时间(s)')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='audit.Account')),
                ('host_user_bind', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='audit.HostUserBind')),
            ],
        ),
    ]
