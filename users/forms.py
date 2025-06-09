from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from subscriptions.models import Plan
from payments.models import Payment
import string
import random

def generate_password(length=12):
    """Génère un mot de passe aléatoire"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for _ in range(length))

class CustomUserCreationForm(UserCreationForm):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        required=True,
        label="Forfait"
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('MOBILE_MONEY', 'Mobile Money'),
            ('CASH', 'Espèces'),
        ],
        required=True,
        label="Méthode de paiement"
    )
    phone_number_mobile_money = forms.CharField(
        max_length=20,
        required=False,
        label="Numéro de téléphone Mobile Money"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone_number', 'address', 'plan', 'payment_method', 'phone_number_mobile_money')
        help_texts = {
            'username': 'Le nom d\'utilisateur doit être unique.',
            'phone_number': 'Numéro de téléphone de l\'utilisateur.',
            'email': 'Adresse email (optionnelle)',
            'address': 'Adresse physique (optionnelle)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer les champs de mot de passe requis
        del self.fields['password1']
        del self.fields['password2']
        
        # Rendre les champs email et adresse optionnels
        self.fields['email'].required = False
        self.fields['address'].required = False
        
        # Personnaliser les messages d'aide
        self.fields['email'].help_text = 'Adresse email (optionnelle)'
        self.fields['address'].help_text = 'Adresse physique (optionnelle)'
        
        # Ajouter les champs email et adresse au formulaire
        self.fields['email'].widget.attrs.update({'class': 'vTextField'})
        self.fields['address'].widget.attrs.update({'class': 'vTextField'})
        self.fields['username'].widget.attrs.update({'class': 'vTextField'})
        self.fields['phone_number'].widget.attrs.update({'class': 'vTextField'})
        self.fields['phone_number_mobile_money'].widget.attrs.update({'class': 'vTextField'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Ignorer complètement la validation d'unicité
            return username
        return None

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        phone_number_mobile_money = cleaned_data.get('phone_number_mobile_money')

        if payment_method == 'MOBILE_MONEY' and not phone_number_mobile_money:
            raise forms.ValidationError("Le numéro de téléphone Mobile Money est requis pour cette méthode de paiement.")

        return cleaned_data

    def save(self, commit=True):
        # Générer un mot de passe aléatoire
        password = generate_password()
        self.cleaned_data['password1'] = password
        self.cleaned_data['password2'] = password
        
        # Créer l'utilisateur avec le mot de passe généré
        user = super().save(commit=False)
        user.plain_password = password
        
        if commit:
            user.save()
        
        return user 