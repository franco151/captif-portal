from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    display_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Nom d'affichage (peut être dupliqué)",
        db_column='display_name'
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Numéro de téléphone obligatoire")
    address = models.TextField(blank=True, null=True, help_text="Adresse (optionnel)")
    email = models.EmailField(blank=True, null=True, help_text="Adresse email (optionnel)")
    last_login_expiry = models.DateTimeField(null=True, blank=True, help_text="Date et heure d'expiration de la dernière connexion")
    session_expiry = models.DateTimeField(null=True, blank=True, help_text="Date et heure d'expiration de la session actuelle")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    plain_password = models.CharField(max_length=128, blank=True, null=True, help_text="Mot de passe en clair pour les reçus")
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        db_table = 'users_user'
        
    def __str__(self):
        return f"{self.display_name or self.username} ({self.phone_number})"

    def clean(self):
        super().clean()
        if not self.phone_number:
            from django.core.exceptions import ValidationError
            raise ValidationError({'phone_number': 'Le numéro de téléphone est obligatoire'}) 