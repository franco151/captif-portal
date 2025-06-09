from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import User
from .forms import CustomUserCreationForm
from subscriptions.models import Subscription
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm
from django.urls import path
from django.template.response import TemplateResponse
import string
import random
import pytz
import os
from io import BytesIO
from django.core.files import File
from django.conf import settings
import qrcode
from PIL import Image

def generate_password(length=12):
    """Génère un mot de passe aléatoire"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for _ in range(length))

# Définir le fuseau horaire de Madagascar
MADAGASCAR_TZ = pytz.timezone('Indian/Antananarivo')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        widgets = {
            'username': forms.TextInput(attrs={'class': 'vTextField'}),
            'email': forms.EmailInput(attrs={'class': 'vTextField'}),
            'phone_number': forms.TextInput(attrs={'class': 'vTextField'}),
            'address': forms.TextInput(attrs={'class': 'vTextField'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Vérifier si l'utilisateur existe déjà
            if self.instance.pk is None:  # Nouvel utilisateur
                if User.objects.filter(username=username).exists():
                    # Si l'utilisateur existe, ajouter un suffixe numérique
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
            return username
        return None

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('display_name', 'username', 'email', 'phone_number', 'address', 'is_staff', 'is_active', 'get_subscription_status')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'display_name', 'email', 'phone_number', 'address')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'display_name', 'password')}),
        ('Informations personnelles', {
            'fields': ('email', 'phone_number', 'address'),
            'description': 'L\'adresse email et l\'adresse sont optionnelles'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'address', 'plan', 'payment_method', 'phone_number_mobile_money'),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print/<int:user_id>/', self.admin_site.admin_view(self.print_receipt), name='print-receipt'),
        ]
        return custom_urls + urls

    def print_receipt(self, request, user_id):
        user = User.objects.get(id=user_id)
        # Recharger l'abonnement et le paiement au cas où ils auraient été modifiés récemment
        subscription = Subscription.objects.filter(user=user).first()
        payment = Payment.objects.filter(user=user).first()
        
        if not subscription or not payment:
            self.message_user(request, "Impossible de générer le reçu : abonnement ou paiement non trouvé.", level='error')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
        # Utiliser le mot de passe stocké
        plain_password = user.plain_password
        if not plain_password:
            # Si pas de mot de passe stocké, en générer un nouveau et le sauvegarder
            plain_password = generate_password()
            user.set_password(plain_password)
            user.plain_password = plain_password
            user.save()
            # Recharger l'utilisateur pour s'assurer que le plain_password est disponible
            user.refresh_from_db()
            plain_password = user.plain_password # S'assurer d'avoir la valeur mise à jour

        # --- Nouvelle logique de génération du QR code à la volée ---
        qr_code_image_data = None
        try:
            # Contenu du QR code (utilisateur et mot de passe)
            qr_content = f"{user.username}:{plain_password}"
            print(f"[DEBUG print_receipt] QR content set to: {qr_content}")
            
            # Générer le QR code dans un buffer en mémoire
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="green", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0) # Rembobiner le buffer pour la lecture
            qr_code_image_data = buffer

            # Optionnel: Sauvegarder le QR code dans le modèle aussi, pour d'autres usages
            # Cela recrée le fichier sur le disque si nécessaire.
            # Utiliser un nom de fichier basé sur l'utilisateur et l'id de l'abonnement
            filename = f'qr_code_{user.username}_{subscription.id}.png'
            # Si on veut S'ASSURER que le champ QR code dans le modèle Subscription a le bon fichier:
            if not subscription.qr_code or not os.path.exists(subscription.qr_code.path) or os.path.basename(subscription.qr_code.name) != filename:
                 print(f"[DEBUG print_receipt] QR code file missing or name mismatch. Saving new file: {filename}")
                 # Utiliser File pour envelopper le buffer et le nom de fichier
                 file_to_save = File(BytesIO(buffer.getvalue()), name=filename)
                 subscription.qr_code.save(filename, file_to_save, save=True) # save=True pour enregistrer l'objet après

            # S'assurer que le buffer est positionné au début pour generate_receipt_pdf
            qr_code_image_data.seek(0)
            
        except Exception as e:
            print(f"[DEBUG print_receipt] Error generating or saving QR code for PDF: {e}")
            qr_code_image_data = None # S'assurer qu'il est None en cas d'erreur
        # --- Fin Nouvelle logique --- 

        # Passer les données du QR code (buffer) à la fonction de génération PDF
        return self.generate_receipt_pdf(user, subscription, payment, plain_password, qr_code_image_data=qr_code_image_data)

    # Restaurer la méthode get_subscription_status qui a été supprimée par erreur
    def get_subscription_status(self, obj):
        subscription = Subscription.objects.filter(user=obj, is_active=True).first()
        if subscription:
            if subscription.end_date < timezone.now():
                subscription.is_active = False
                subscription.save()
                return "Expiré"
            return "Actif"
        return "Pas d'abonnement"
    get_subscription_status.short_description = "État de l'abonnement"

    # Modifier la signature pour accepter les données de l'image QR code
    def generate_receipt_pdf(self, user, subscription, payment, plain_password, qr_code_image_data=None):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{user.username}.pdf"'
        
        # Définir les dimensions en millimètres (standard pour les tickets)
        width = 80 * mm  # Largeur standard pour les tickets
        height = 300 * mm  # Une grande hauteur pour permettre un contenu variable
        
        # Créer le canvas avec les dimensions personnalisées
        # Utiliser portrait pour une imprimante ticket
        p = canvas.Canvas(response, pagesize=(width, height))
        
        # Couleurs (utiliser des couleurs adaptées à l'impression thermique si possible, sinon gris)
        # Pour l'impression thermique, les couleurs sont généralement converties en nuances de gris/noir.
        # Utilisons du noir et un gris foncé pour le texte.
        primary_color_rgb = (0, 0, 0)       # Noir (for general text)
        title_color_rgb = (0, 0, 0.5)   # Dark Blue (for titles)
        watermark_color_rgb = (0.9, 0.9, 0.9) # Gris très clair pour la filigrane
        header_bg_color_rgb = (0.8, 0.9, 1.0) # Bleu très clair pour l'en-tête
        header_text_color_rgb = (0, 0, 0.5) # Bleu foncé pour le texte de l'en-tête

        # Marges et espacements (réduits pour un ticket)
        margin_left = 2 * mm
        margin_right = 2 * mm
        margin_top = 5 * mm
        margin_bottom = 5 * mm
        content_width = width - (margin_left + margin_right)
        
        # Position de départ pour le contenu
        y_position = height - margin_top
        line_height = 4*mm  # Restauré à 4mm pour une meilleure lisibilité
        small_line_height = 3*mm # Restauré à 3mm pour une meilleure lisibilité
        
        # --- Filigrane (positionné en premier pour être en arrière-plan) ---
        # On place la filigrane en diagonal sur toute la page
        p.setFillColorRGB(*watermark_color_rgb) # Couleur très claire
        p.setFont("Helvetica", 16) # Taille réduite pour le filigrane
        
        # Sauvegarder l'état actuel du canvas
        p.saveState()
        
        # Rotation de 45 degrés
        p.translate(width/2, height/2)  # Déplacer au centre
        p.rotate(45)  # Rotation de 45 degrés
        
        # Dessiner le filigrane plusieurs fois pour couvrir toute la page
        watermark_text = "BestConnect by Franco Fanazava"
        text_width = p.stringWidth(watermark_text, "Helvetica", 16)
        
        # Calculer les positions pour couvrir toute la page
        # Ajuster les coordonnées pour mieux aligner avec le contenu
        start_x = -width * 0.8
        start_y = -height * 0.8
        spacing = text_width * 2  # Augmenter l'espacement entre les répétitions
        
        # Dessiner le filigrane en diagonale avec une opacité réduite
        p.setFillColorRGB(0.95, 0.95, 0.95)  # Presque blanc pour un effet plus subtil
        
        # Dessiner le filigrane en diagonale
        for y in range(int(start_y), int(height*1.6), int(spacing)):
            for x in range(int(start_x), int(width*1.6), int(spacing)):
                p.drawString(x, y, watermark_text)
        
        # Restaurer l'état du canvas
        p.restoreState()

        # --- En-tête avec fond bleu ---
        header_height = 15 * mm  # Réduit pour un en-tête plus compact
        header_y_start = height - margin_top
        header_y_end = header_y_start - header_height

        # Dessiner le rectangle de fond bleu
        p.setFillColorRGB(*header_bg_color_rgb)
        p.rect(margin_left, header_y_end, width - (margin_left + margin_right), header_height, fill=1)

        # Texte de l'en-tête
        p.setFillColorRGB(*header_text_color_rgb)
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width/2, header_y_start - 5*mm, "BestConnect")
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, header_y_start - 10*mm, "Reçu d'inscription")

        # Mettre à jour la position Y après l'en-tête
        y_position = header_y_end - 3*mm

        # Ligne de séparation après l'en-tête
        p.setStrokeColorRGB(*header_text_color_rgb)
        p.line(margin_left, y_position, width - margin_right, y_position)
        y_position -= line_height

        # Fonction pour dessiner un titre de section
        def draw_section_title(title):
            nonlocal y_position
            y_position -= small_line_height # Réduit l'espace avant le titre
            p.setFillColorRGB(*title_color_rgb)
            p.setFont("Helvetica-Bold", 8)
            p.drawCentredString(width/2, y_position, title.upper())
            y_position -= line_height # Réduit l'espace après le titre
        
        # Fonction pour dessiner une ligne d'information
        def draw_info_line(label, value, is_bold_value=False):
            nonlocal y_position
            p.setFillColorRGB(*primary_color_rgb)
            p.setFont("Helvetica", 7)
            p.drawString(margin_left, y_position, f"{label}:")
            
            # Calculer la largeur du label pour aligner la valeur
            label_width = p.stringWidth(label + ":", "Helvetica", 7)
            value_x = margin_left + label_width + 1*mm # Réduit l'espace après le label
            
            if is_bold_value:
                 p.setFont("Helvetica-Bold", 7)
            else:
                 p.setFont("Helvetica", 7)
                 
            # Utiliser un TextObject pour gérer le texte long automatiquement
            text_object = p.beginText(value_x, y_position)
            text_object.setFont("Helvetica" if not is_bold_value else "Helvetica-Bold", 7)
            text_object.textLine(str(value))
            p.drawText(text_object)

            y_position -= small_line_height # Réduit l'espacement vertical entre les lignes

        # Informations utilisateur
        draw_section_title("Informations utilisateur")
        draw_info_line("Nom d'utilisateur", user.username, is_bold_value=True)
        draw_info_line("Mot de passe", plain_password, is_bold_value=True)
        draw_info_line("Email", user.email or "Non renseigné")
        draw_info_line("Téléphone", user.phone_number)
        draw_info_line("Adresse", user.address or "Non renseignée")
        y_position -= small_line_height # Réduit l'espace après la section (au lieu de small_line_height * 2)

        # Informations abonnement
        draw_section_title("Détails de l'abonnement")
        draw_info_line("Forfait", subscription.plan.name, is_bold_value=True)
        draw_info_line("Prix", f"{subscription.plan.price:,} Ar", is_bold_value=True)
        
        # Convertir les dates en heure locale de Madagascar
        try:
            MADAGASCAR_TZ = pytz.timezone('Indian/Antananarivo')
        except pytz.UnknownTimeZoneError:
            MADAGASCAR_TZ = timezone.get_default_timezone()
            
        start_date = subscription.start_date.astimezone(MADAGASCAR_TZ)
        end_date = subscription.end_date.astimezone(MADAGASCAR_TZ)
        payment_date = payment.created_at.astimezone(MADAGASCAR_TZ)
        
        draw_info_line("Date d'inscription", start_date.strftime('%d/%m/%Y'))
        draw_info_line("Date d'expiration", end_date.strftime('%d/%m/%Y'))
        y_position -= small_line_height # Réduit l'espace après la section (au lieu de small_line_height * 2)
        
        # Informations paiement
        draw_section_title("Informations de paiement")
        draw_info_line("Méthode de paiement", payment.get_payment_method_display())
        draw_info_line("Numéro de téléphone", payment.phone_number)
        draw_info_line("Date de paiement", payment_date.strftime('%d/%m/%Y %H:%M'))
        
        # Ajouter la date de génération du document
        current_time = timezone.now().astimezone(MADAGASCAR_TZ)
        draw_info_line("Document généré le", current_time.strftime('%d/%m/%Y à %H:%M'))
        y_position -= line_height # Réduit l'espace avant le QR code (au lieu de line_height * 2)
        
        # QR Code centré
        if qr_code_image_data:
            print(f"[DEBUG generate_receipt_pdf] Attempting to draw QR code from buffer...")
            qr_size = 50*mm
            qr_x = (width - qr_size) / 2
            footer_height = small_line_height * 2 + line_height  # Réduit la hauteur du footer
            min_y_for_qr = margin_bottom + footer_height + 2*mm  # Réduit l'espace
            qr_y = max(min_y_for_qr, y_position - qr_size)
            
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(qr_code_image_data)
                p.drawImage(img_reader, qr_x, qr_y, width=qr_size, height=qr_size)
                y_position = qr_y - 2*mm  # Réduit l'espace après le QR code
                print(f"[DEBUG generate_receipt_pdf] QR code drawn successfully from buffer.")
            except Exception as e:
                print(f"[DEBUG generate_receipt_pdf] Error drawing QR code from data buffer: {e}")
                p.setFillColorRGB(1, 0, 0)
                p.setFont("Helvetica-Bold", 7)
                p.drawCentredString(width/2, y_position - 10*mm, "Erreur Affichage QR")
                y_position -= 15*mm
        else:
            print(f"[DEBUG generate_receipt_pdf] No QR code data provided to draw.")
            p.setFillColorRGB(1, 0, 0)
            p.setFont("Helvetica-Bold", 7)
            p.drawCentredString(width/2, y_position - 10*mm, "QR Code manquant")
            y_position -= 15*mm

        # Pied de page avec fond bleu clair
        footer_height = small_line_height * 2 + line_height  # Réduit la hauteur du footer
        footer_y_start = margin_bottom + 5*mm  # Réduit l'espace
        final_footer_y = max(footer_y_start, y_position - footer_height)

        # Rectangle de fond pour le pied de page
        p.setFillColorRGB(*header_bg_color_rgb)
        p.rect(margin_left, final_footer_y - 6*mm, width - (margin_left + margin_right), 6*mm, fill=1)  # Réduit la hauteur

        # Texte du pied de page
        p.setFillColorRGB(*header_text_color_rgb)
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(width/2, final_footer_y + small_line_height, "Merci de votre confiance")
        p.setFont("Helvetica", 7)
        p.drawCentredString(width/2, final_footer_y + small_line_height*0.5, "BestConnect - Votre partenaire de confiance")
        p.drawCentredString(width/2, final_footer_y, "Pour toute assistance: 034 72 497 15")

        # Finaliser la page
        p.showPage()
        p.save()
        
        return response

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            # Générer un mot de passe aléatoire
            plain_password = generate_password()
            obj.set_password(plain_password)
            obj.plain_password = plain_password  # Stocker le mot de passe en clair
            
            # Sauvegarder l'utilisateur
            super().save_model(request, obj, form, change)
            
            plan = form.cleaned_data.get('plan')
            if plan is None:
                raise ValueError("Le forfait est obligatoire.")
                
            payment_method = form.cleaned_data.get('payment_method')
            phone_number_mobile_money = form.cleaned_data.get('phone_number_mobile_money')
            
            # Utiliser le fuseau horaire de Madagascar
            try:
                MADAGASCAR_TZ = pytz.timezone('Indian/Antananarivo')
            except pytz.UnknownTimeZoneError:
                MADAGASCAR_TZ = timezone.get_default_timezone()

            start_date = timezone.now().astimezone(MADAGASCAR_TZ)
            end_date = start_date + timedelta(days=plan.get_duration_in_days())
            
            # Vérifier si un abonnement existe déjà
            existing_subscription = Subscription.objects.filter(user=obj).first()
            if existing_subscription:
                existing_subscription.delete()
            
            subscription = Subscription.objects.create(
                user=obj,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            # Créer le paiement
            payment = Payment.objects.create(
                user=obj,
                plan=plan,
                amount=plan.price,
                payment_method=payment_method,
                phone_number=phone_number_mobile_money if payment_method == 'MOBILE_MONEY' else obj.phone_number,
                status='SUCCESS'
            )

            # Pour une nouvelle création, générer et sauvegarder le QR code ici
            # Utiliser la même logique que dans print_receipt pour la génération en mémoire et la sauvegarde
            qr_code_image_data = None
            try:
                qr_content = f"{obj.username}:{plain_password}"
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)
                img = qr.make_image(fill_color="green", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                qr_code_image_data = buffer
                
                # Sauvegarder le fichier QR code dans le modèle de l'abonnement
                filename = f'qr_code_{obj.username}_{subscription.id}.png'
                file_to_save = File(BytesIO(buffer.getvalue()), name=filename)
                subscription.qr_code.save(filename, file_to_save, save=True) # save=True pour enregistrer l'abonnement avec le QR code
                
            except Exception as e:
                 print(f"Error generating and saving QR code during user creation: {e}")
                 # Gérer l'erreur de manière appropriée si la sauvegarde du QR code est critique
                 pass # Pour l'instant, on continue même sans QR code si la génération échoue

            # Générer et retourner le reçu PDF avec le mot de passe en clair et les données du QR code
            # S'assurer que subscription object est à jour si le QR code a été sauvegardé dessus
            subscription.refresh_from_db()
            return self.generate_receipt_pdf(obj, subscription, payment, plain_password, qr_code_image_data=qr_code_image_data)

        else:
            # Pour une modification, sauvegarder normalement
            super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        user = self.get_object(request, object_id)
        subscription = Subscription.objects.filter(user=user).first()
        payment = Payment.objects.filter(user=user).first()
        
        if subscription and payment:
            extra_context['show_print_button'] = True
        
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

admin.site.register(User, CustomUserAdmin) 