from celery import shared_task
from django.utils import timezone
from .models import Subscription, Statistics

@shared_task
def update_subscription_status():
    """Met à jour le statut des abonnements expirés"""
    expired_subscriptions = Subscription.objects.filter(
        is_active=True,
        end_date__lt=timezone.now()
    )
    expired_subscriptions.update(is_active=False)

@shared_task
def generate_daily_statistics():
    """Génère les statistiques quotidiennes"""
    Statistics.generate_daily_stats()

@shared_task
def check_connectivity():
    """Vérifie la connectivité des utilisateurs"""
    from django.conf import settings
    import requests
    
    active_subscriptions = Subscription.objects.filter(is_active=True)
    for subscription in active_subscriptions:
        try:
            # Vérifier la connectivité via l'API du portail captif
            response = requests.get(
                f"{settings.CAPTIVE_PORTAL_API_URL}/check_connection",
                params={'username': subscription.user.username},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # Mettre à jour le statut de connexion si nécessaire
                if not data.get('is_connected'):
                    subscription.is_active = False
                    subscription.save()
        except requests.RequestException:
            # En cas d'erreur de connexion, on considère l'utilisateur comme déconnecté
            subscription.is_active = False
            subscription.save() 