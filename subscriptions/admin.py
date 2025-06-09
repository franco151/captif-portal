from django.contrib import admin
from .models import Plan, Subscription
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from django.http import HttpResponse, HttpResponseRedirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, mm
from reportlab.lib.units import mm
from django.urls import path
from django.template.response import TemplateResponse
from users.models import User
from payments.models import Payment
from . import views # Importez les vues ici

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'duration', 'duration_unit', 'price', 'is_active')
    list_filter = ('is_active', 'duration_unit')
    search_fields = ('name', 'description')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('plan', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'start_date'
    actions = ['export_as_pdf']
    readonly_fields = ('qr_code',)
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user',)
        }),
        ('Détails de l\'abonnement', {
            'fields': ('plan', 'start_date', 'end_date', 'is_active')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Vérifier le statut de chaque abonnement
        for subscription in queryset:
            subscription.check_status()
        return queryset

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Définir l'URL d'impression ici, en utilisant object_id
            path('<int:object_id>/print/', self.admin_site.admin_view(views.print_subscription_receipt), name='print-subscription-receipt'),
        ]
        # Insérer nos URLs personnalisées au début de la liste des URLs par défaut
        return custom_urls + urls

    def generate_subscription_pdf(self, request, subscription_id):
        subscription = self.get_object(request, subscription_id)
        return subscription.generate_pdf()

    def generate_receipt_pdf_view(self, request, subscription_id):
        subscription = self.get_object(request, subscription_id)
        user = subscription.user
        payment = Payment.objects.filter(user=user).first()
        
        if not payment:
            self.message_user(request, "Impossible de générer le reçu : paiement non trouvé.", level='error')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
        # Générer un nouveau mot de passe pour le reçu
        from users.admin import generate_password
        plain_password = generate_password()
        user.set_password(plain_password)
        user.save()
        
        return self._generate_receipt_pdf(user, subscription, payment, plain_password)

    def _generate_receipt_pdf(self, user, subscription, payment, plain_password):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{user.username}.pdf"'
        
        # Définir les dimensions en millimètres
        width = 80 * mm  # Largeur standard pour les tickets
        height = 297 * mm  # Hauteur A4
        
        # Créer le canvas avec les dimensions personnalisées
        p = canvas.Canvas(response, pagesize=(width, height))
        
        # Couleurs
        primary_color = (0.26, 0.46, 0.56)  # Bleu BestConnect
        secondary_color = (0.2, 0.2, 0.2)   # Gris foncé
        
        # Marges et espacements
        margin_left = 3 * mm
        margin_right = 3 * mm
        margin_top = 3 * mm
        margin_bottom = 3 * mm
        content_width = width - (margin_left + margin_right)
        
        # En-tête avec logo et titre
        p.setFillColorRGB(*primary_color)
        header_height = 15 * mm
        p.rect(0, height - header_height, width, header_height, fill=True)
        
        # Calculer les positions verticales pour un centrage parfait
        header_center = height - (header_height / 2)
        title_spacing = 4 * mm
        
        p.setFillColorRGB(1, 1, 1)  # Texte blanc
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width/2, header_center + title_spacing/2, "BestConnect")
        
        p.setFont("Helvetica-Bold", 9)
        p.drawCentredString(width/2, header_center - title_spacing/2, "Reçu d'inscription")
        
        # Position de départ pour le contenu
        y_position = height - header_height - 5*mm
        line_height = 4*mm
        
        # Fonction pour dessiner une ligne d'information
        def draw_info_line(label, value):
            nonlocal y_position
            p.setFillColorRGB(*secondary_color)
            p.setFont("Helvetica-Bold", 7)
            p.drawString(margin_left, y_position, f"{label}:")
            p.setFont("Helvetica", 7)
            label_width = p.stringWidth(label + ":", "Helvetica-Bold", 7)
            value_x = margin_left + label_width + 2*mm
            max_value_width = content_width - (label_width + 4*mm)
            value = str(value)
            while p.stringWidth(value, "Helvetica", 7) > max_value_width and len(value) > 0:
                value = value[:-1]
            p.drawString(value_x, y_position, value)
            y_position -= line_height
        
        # Fonction pour dessiner un titre de section
        def draw_section_title(title):
            nonlocal y_position
            y_position -= line_height/2
            p.setFillColorRGB(*primary_color)
            p.setFont("Helvetica-Bold", 8)
            p.drawCentredString(width/2, y_position, title)
            y_position -= line_height
        
        # Informations utilisateur
        draw_section_title("Informations utilisateur")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Nom d'utilisateur", user.username)
        draw_info_line("Mot de passe", plain_password)
        draw_info_line("Email", user.email or "Non renseigné")
        draw_info_line("Téléphone", user.phone_number)
        draw_info_line("Adresse", user.address or "Non renseignée")
        
        # Informations abonnement
        draw_section_title("Détails de l'abonnement")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Forfait", subscription.plan.name)
        draw_info_line("Prix", f"{subscription.plan.price:,} Ar")
        draw_info_line("Date d'inscription", subscription.start_date.strftime('%d/%m/%Y'))
        draw_info_line("Date d'expiration", subscription.end_date.strftime('%d/%m/%Y'))
        
        # Informations paiement
        draw_section_title("Informations de paiement")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Méthode de paiement", payment.get_payment_method_display())
        draw_info_line("Numéro de téléphone", payment.phone_number)
        draw_info_line("Date de paiement", payment.created_at.strftime('%d/%m/%Y %H:%M'))
        
        # Espace avant le QR code
        y_position -= line_height/2
        
        # QR Code centré en bas
        if subscription.qr_code:
            max_qr_size = min(content_width, 45*mm)
            qr_x = (width - max_qr_size) / 2
            qr_y = y_position - max_qr_size
            p.drawImage(subscription.qr_code.path, qr_x, qr_y, width=max_qr_size, height=max_qr_size)
            
            # Message de remerciement sous le QR code
            p.setFillColorRGB(*primary_color)
            p.setFont("Helvetica-Bold", 7)
            p.drawCentredString(width/2, qr_y - 8*mm, "Merci de votre confiance")
            p.setFont("Helvetica", 6)
            p.drawCentredString(width/2, qr_y - 11*mm, "BestConnect - Votre partenaire de confiance")
            p.drawCentredString(width/2, qr_y - 14*mm, "Pour toute assistance: 034 72 497 15")
        
        p.showPage()
        p.save()
        
        return response

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        subscription = self.get_object(request, object_id)
        
        if subscription:
            extra_context['show_print_button'] = True
        
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def export_as_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="subscriptions.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # En-tête
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 50, "Liste des abonnements")
        
        # Contenu
        y = height - 100
        p.setFont("Helvetica", 12)
        for subscription in queryset:
            p.drawString(50, y, f"Utilisateur: {subscription.user.username}")
            p.drawString(50, y - 20, f"Forfait: {subscription.plan.name}")
            p.drawString(50, y - 40, f"Date de début: {subscription.start_date.strftime('%d/%m/%Y')}")
            p.drawString(50, y - 60, f"Date de fin: {subscription.end_date.strftime('%d/%m/%Y')}")
            p.drawString(50, y - 80, f"Statut: {'Actif' if subscription.is_active else 'Expiré'}")
            y -= 120
            
            if y < 100:  # Nouvelle page si nécessaire
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 12)
        
        p.showPage()
        p.save()
        return response
    export_as_pdf.short_description = "Exporter les abonnements sélectionnés en PDF" 