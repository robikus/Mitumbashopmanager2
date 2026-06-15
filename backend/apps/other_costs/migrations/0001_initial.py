from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OtherCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('category', models.CharField(choices=[('rent', 'Rent'), ('wages', 'Wages'), ('tax', 'Tax'), ('loan_repayment', 'Loan Repayment'), ('extra_repayment', 'Extra Repayment'), ('other', 'Other')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='other_costs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'other_cost',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='othercost',
            index=models.Index(fields=['user', 'date'], name='other_cost_user_id_date_idx'),
        ),
    ]
