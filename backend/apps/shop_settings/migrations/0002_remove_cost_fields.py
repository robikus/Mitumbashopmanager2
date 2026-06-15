from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop_settings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(model_name='shopsettings', name='rent'),
        migrations.RemoveField(model_name='shopsettings', name='wages'),
        migrations.RemoveField(model_name='shopsettings', name='other'),
        migrations.RemoveField(model_name='shopsettings', name='tax'),
        migrations.RemoveField(model_name='shopsettings', name='loan_monthly'),
        migrations.RemoveField(model_name='shopsettings', name='loan_months_paid'),
    ]
