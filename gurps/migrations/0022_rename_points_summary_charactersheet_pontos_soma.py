# Generated by Django 5.1.2 on 2024-11-27 14:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0021_rename_appearance_age_charactersheet_aparencia_idade'),
    ]

    operations = [
        migrations.RenameField(
            model_name='charactersheet',
            old_name='points_summary',
            new_name='pontos_soma',
        ),
    ]