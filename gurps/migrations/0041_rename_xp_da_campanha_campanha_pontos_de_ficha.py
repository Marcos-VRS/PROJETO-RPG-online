# Generated by Django 5.1.2 on 2025-02-20 07:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0040_rename_xp_inicial_campanha_xp_da_campanha'),
    ]

    operations = [
        migrations.RenameField(
            model_name='campanha',
            old_name='xp_da_campanha',
            new_name='pontos_de_ficha',
        ),
    ]
