from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0006_remove_payment_date'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DROP VIEW IF EXISTS payments_daily_stats;
            DROP VIEW IF EXISTS payments_monthly_stats;
            DROP VIEW IF EXISTS payments_yearly_stats;
            """,
            reverse_sql=""
        ),
    ] 