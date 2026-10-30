from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gurps", "0074_videogenrequest_render_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="videobeat",
            name="progress_pct",
            field=models.IntegerField(default=-1),
        ),
    ]
