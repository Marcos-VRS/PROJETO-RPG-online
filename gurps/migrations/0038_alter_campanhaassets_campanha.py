# Generated by Django 5.1.2 on 2025-02-18 18:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0037_alter_campanhaassets_campanha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campanhaassets',
            name='campanha',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='gurps.campanha'),
        ),
    ]
