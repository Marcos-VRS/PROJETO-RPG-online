# Generated by Django 5.1.2 on 2025-03-31 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0048_campanhaassets_show'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campanhaassets',
            name='show',
            field=models.BooleanField(default=True),
        ),
    ]
