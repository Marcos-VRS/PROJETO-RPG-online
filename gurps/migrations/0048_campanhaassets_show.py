# Generated by Django 5.1.2 on 2025-03-31 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0047_alter_campanhaassets_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='campanhaassets',
            name='show',
            field=models.BooleanField(default=False),
        ),
    ]
