from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_simplify_dates'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='payment_date',
        ),
    ] 