from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_userprofile_last_payment"),
    ]

    operations = [
        migrations.CreateModel(
            name="SigninPageConfig",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("mpesa_phone", models.CharField(default="0700 000 000", max_length=30)),
                ("price", models.PositiveIntegerField(default=300)),
            ],
            options={
                "db_table": "auth_signin_page_config",
                "verbose_name": "Signin Page",
                "verbose_name_plural": "Signin Page",
            },
        ),
    ]
