# Generated by Django 5.1.2 on 2025-03-24 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0045_alter_campanhaassets_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campanhaassets',
            name='name',
            field=models.CharField(max_length=300),
        ),
    ]
