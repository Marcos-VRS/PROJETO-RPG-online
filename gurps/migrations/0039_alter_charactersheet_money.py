# Generated by Django 5.1.2 on 2025-02-20 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0038_alter_campanhaassets_campanha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charactersheet',
            name='money',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
