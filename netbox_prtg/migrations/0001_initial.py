from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Prtg",
            fields=[],
            options={
                "managed": False,
                "default_permissions": (),
                "permissions": (
                    ("configure_prtg", "Can configure PRTG plugin settings"),
                ),
            },
        ),
    ]
