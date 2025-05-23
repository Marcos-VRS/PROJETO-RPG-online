# Generated by Django 5.1.2 on 2025-04-23 15:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0053_alter_campanhaassets_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='SaveState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('campanha', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saves', to='gurps.campanha')),
            ],
        ),
    ]
