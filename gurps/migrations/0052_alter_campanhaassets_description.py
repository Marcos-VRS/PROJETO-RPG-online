# Generated by Django 5.1.2 on 2025-04-15 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0051_alter_campanha_descricao_alter_campanha_regras'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campanhaassets',
            name='description',
            field=models.TextField(blank=True, max_length=2000, null=True),
        ),
    ]
