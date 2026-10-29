from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gurps", "0073_videobeat_fidelity_videobeat_ref_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="videogenrequest",
            name="render_style",
            field=models.CharField(
                choices=[("anime", "Anime"), ("realism", "Realista")],
                default="anime",
                max_length=16,
            ),
        ),
    ]
