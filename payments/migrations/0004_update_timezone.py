from django.db import migrations
from django.utils import timezone
import pytz

def update_timezone_awareness(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    madagascar_tz = pytz.timezone('Indian/Antananarivo')
    
    for payment in Payment.objects.all():
        if payment.payment_date and not timezone.is_aware(payment.payment_date):
            payment.payment_date = madagascar_tz.localize(payment.payment_date)
            payment.save()

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_timezone_awareness),
    ] 