from django.core.management.base import BaseCommand
from portal.models import Plan

class Command(BaseCommand):
    help = 'Crée des données de test pour l\'application'

    def handle(self, *args, **kwargs):
        # Création des plans
        plans = [
            {
                'name': 'Basique',
                'description': 'Accès Internet basique - 5 Mbps',
                'price': 9.99,
                'duration_days': 30,
            },
            {
                'name': 'Standard',
                'description': 'Accès Internet standard - 20 Mbps',
                'price': 19.99,
                'duration_days': 30,
            },
            {
                'name': 'Premium',
                'description': 'Accès Internet premium - 50 Mbps',
                'price': 29.99,
                'duration_days': 30,
            },
        ]

        for plan_data in plans:
            Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'Plan créé : {plan_data["name"]}')
            ) 