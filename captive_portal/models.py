from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
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
        
        # Calculer le temps restant (par exemple, 24 heures)
        end_time = self.start_time + timedelta(hours=24)
        remaining = end_time - timezone.now()
        
        if remaining.total_seconds() <= 0:
            self.end_session()
            return 0
        
        return int(remaining.total_seconds() / 60)  # Retourne le temps restant en minutes 