# Generated by Django 5.1.2 on 2024-11-27 06:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0018_rename_name_charactersheet_nome_personagem'),
    ]

    operations = [
        migrations.RenameField(
            model_name='charactersheet',
            old_name='nome_personagem',
            new_name='name',
        ),
    ]
