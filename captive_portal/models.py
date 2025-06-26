from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    mac_address = models.CharField(max_length=17, null=True, blank=True)  # Format XX:XX:XX:XX:XX:XX
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Session de {self.user.username} ({self.start_time})"
    
    def end_session(self):
        self.end_time = timezone.now()
        self.is_active = False
        self.save()
    
    def get_remaining_time(self):
        if not self.is_active:
            return 0
        
        # Importer ici pour éviter les imports circulaires
        from subscriptions.models import Subscription
        
        # Récupérer l'abonnement actif de l'utilisateur
        subscription = Subscription.objects.filter(
            user=self.user,
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        if not subscription:
            # Pas d'abonnement actif, terminer la session
            self.end_session()
            return 0
        
        # Calculer le temps restant basé sur la date d'expiration de l'abonnement
        remaining = subscription.end_date - timezone.now()
        
        if remaining.total_seconds() <= 0:
            # L'abonnement a expiré, terminer la session
            self.end_session()
            # Marquer l'abonnement comme inactif
            subscription.is_active = False
            subscription.save()
            return 0
        
        return int(remaining.total_seconds() / 60)  # Retourne le temps restant en minutes
    
    @classmethod
    def check_mac_address_usage(cls, user, mac_address):
        """Vérifie si l'adresse MAC est déjà utilisée par cet utilisateur"""
        if not mac_address:
            return False
        
        existing_session = cls.objects.filter(
            user=user,
            mac_address=mac_address,
            is_active=True
        ).first()
        
        return existing_session is not None
    
    @classmethod
    def get_active_session_by_mac(cls, user, mac_address):
        """Récupère la session active pour cette adresse MAC"""
        return cls.objects.filter(
            user=user,
            mac_address=mac_address,
            is_active=True
        ).first()
    
    @classmethod
    def has_active_session_on_different_device(cls, user, current_mac_address):
        """Vérifie si l'utilisateur a déjà une session active sur un autre appareil"""
        if not current_mac_address:
            return False
        
        existing_session = cls.objects.filter(
            user=user,
            is_active=True
        ).exclude(mac_address=current_mac_address).first()
        
        return existing_session is not None


class NetworkActivity(models.Model):
    ACTIVITY_TYPES = [
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('DATA_TRANSFER', 'Transfert de données'),
        ('BANDWIDTH_LIMIT', 'Limite de bande passante atteinte'),
        ('SUSPICIOUS_ACTIVITY', 'Activité suspecte'),
        ('DEVICE_CHANGE', 'Changement d\'appareil'),
    ]
    
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, null=True, blank=True)
    bytes_uploaded = models.BigIntegerField(default=0)
    bytes_downloaded = models.BigIntegerField(default=0)
    bandwidth_usage = models.FloatField(default=0.0)  # Mbps
    location_data = models.JSONField(null=True, blank=True)  # Géolocalisation si disponible
    user_agent = models.TextField()
    additional_data = models.JSONField(null=True, blank=True)  # Données supplémentaires
    
    class Meta:
        verbose_name = 'Activité Réseau'
        verbose_name_plural = 'Activités Réseau'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.session.user.username} - {self.get_activity_type_display()} - {self.timestamp}"
    
    @property
    def total_data_transfer(self):
        return self.bytes_uploaded + self.bytes_downloaded
    
    @property
    def data_transfer_mb(self):
        return self.total_data_transfer / (1024 * 1024)

class DeviceFingerprint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17, unique=True)
    device_name = models.CharField(max_length=100, null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)  # Mobile, Desktop, Tablet
    operating_system = models.CharField(max_length=100, null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    screen_resolution = models.CharField(max_length=20, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Empreinte d\'appareil'
        verbose_name_plural = 'Empreintes d\'appareils'
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name or self.mac_address}"

class BandwidthUsage(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    upload_speed = models.FloatField()  # Mbps
    download_speed = models.FloatField()  # Mbps
    total_uploaded = models.BigIntegerField()  # Bytes
    total_downloaded = models.BigIntegerField()  # Bytes
    ping_latency = models.FloatField(null=True, blank=True)  # ms
    
    class Meta:
        verbose_name = 'Utilisation de la bande passante'
        verbose_name_plural = 'Utilisations de la bande passante'
        ordering = ['-timestamp']