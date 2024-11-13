# Generated by Django 5.1.2 on 2024-11-11 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gurps', '0005_campanha_regras_campanha_tl_campanha_xp_acumulado_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='basic_lift_lbs',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='basic_move',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='basic_speed',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='damage',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='dx',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='fp',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='hp',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='ht',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='iq',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='perception',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='st',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='will',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='xpdx',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='xpht',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='xpiq',
        ),
        migrations.RemoveField(
            model_name='fichapersonagem',
            name='xpst',
        ),
        migrations.AddField(
            model_name='campanha',
            name='fichas_players',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='campanha',
            name='pontos_de_desvantagens',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fichapersonagem',
            name='attributes',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fichapersonagem',
            name='subattributes',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fichapersonagem',
            name='advantages',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fichapersonagem',
            name='disadvantages',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fichapersonagem',
            name='equipments',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fichapersonagem',
            name='skills',
            field=models.JSONField(blank=True, null=True),
        ),
    ]