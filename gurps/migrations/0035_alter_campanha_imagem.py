# Generated by Django 5.1.2 on 2025-02-08 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0034_alter_campanha_imagem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campanha',
            name='imagem',
            field=models.ImageField(default=None, upload_to='campanhas/'),
        ),
    ]
