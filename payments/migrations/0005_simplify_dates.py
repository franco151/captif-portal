from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_update_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payment_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ] 