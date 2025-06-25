from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from datetime import timedelta, datetime
import logging
from django.db import connection

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CASH', 'Espèces'),
        ('CHECK', 'Chèque'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('SUCCESS', 'Réussi'),
        ('FAILED', 'Échoué'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey('subscriptions.Plan', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='MOBILE_MONEY')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    # payment_date a été supprimé, utiliser created_at à la place
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.receipt_number} - {self.user.username} - {self.amount} Ar"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def generate_receipt_pdf(self):
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from django.db.models import Count, Sum

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{self.receipt_number}.pdf"'

        # Définir les dimensions en millimètres
        width = 210 * mm  # Largeur A4
        height = 297 * mm  # Hauteur A4

        # Créer le canvas avec les dimensions A4
        p = canvas.Canvas(response, pagesize=(width, height))

        # Couleurs
        primary_color = (0.26, 0.46, 0.56)  # Bleu BestConnect
        secondary_color = (0.2, 0.2, 0.2)   # Gris foncé

        # Marges et espacements
        margin_left = 20 * mm
        margin_right = 20 * mm
        margin_top = 20 * mm
        margin_bottom = 20 * mm
        content_width = width - (margin_left + margin_right)

        # En-tête avec logo et titre
        p.setFillColorRGB(*primary_color)
        header_height = 30 * mm
        p.rect(0, height - header_height, width, header_height, fill=True)

        # Titre en blanc
        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 15*mm, "BEST CONNECT")
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 25*mm, "Reçu de Paiement")

        # Position verticale pour le contenu
        y_position = height - header_height - 10*mm

        # Fonction pour dessiner une ligne d'information
        def draw_info_line(label, value):
            nonlocal y_position
            p.setFillColorRGB(*secondary_color)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin_left, y_position, f"{label}:")
            p.setFont("Helvetica", 10)
            p.drawString(margin_left + 40*mm, y_position, str(value))
            y_position -= 6*mm

        # Fonction pour dessiner un titre de section
        def draw_section_title(title):
            nonlocal y_position
            y_position -= 4*mm
            p.setFillColorRGB(*primary_color)
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin_left, y_position, title)
            y_position -= 6*mm

        # Informations du reçu
        draw_section_title("Informations du Reçu")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Numéro de reçu", self.receipt_number)
        draw_info_line("Date", self.created_at.strftime('%d/%m/%Y %H:%M'))

        # Informations client
        draw_section_title("Informations Client")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Nom d'utilisateur", self.user.username)
        draw_info_line("Email", self.user.email)
        draw_info_line("Téléphone", self.phone_number or "Non renseigné")

        # Détails du forfait
        draw_section_title("Détails du Forfait")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Nom du forfait", self.plan.name)
        draw_info_line("Description", self.plan.description)
        draw_info_line("Durée", f"{self.plan.duration} {self.plan.get_duration_unit_display()}")
        draw_info_line("Prix unitaire", f"{self.plan.price:,} Ar")

        # Statistiques du forfait
        from subscriptions.models import Subscription
        active_subscriptions = Subscription.objects.filter(
            plan=self.plan,
            is_active=True
        ).count()
        
        total_amount = Payment.objects.filter(
            plan=self.plan,
            status='SUCCESS'
        ).aggregate(total=Sum('amount'))['total'] or 0

        draw_section_title("Statistiques du Forfait")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Effectif actuel", f"{active_subscriptions} abonnés")
        draw_info_line("Montant total", f"{total_amount:,} Ar")

        # Détails du paiement
        draw_section_title("Détails du Paiement")
        p.setFillColorRGB(*secondary_color)
        draw_info_line("Montant payé", f"{self.amount:,} Ar")
        draw_info_line("Méthode de paiement", self.get_payment_method_display())
        draw_info_line("Statut", self.get_status_display())

        # Pied de page
        footer_y = margin_bottom
        p.setFillColorRGB(*primary_color)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(width/2, footer_y + 15*mm, "Merci de votre confiance !")
        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, footer_y + 10*mm, "BestConnect - Votre connexion internet de confiance")
        p.drawCentredString(width/2, footer_y + 5*mm, "Contact: 034 72 497 15")

        # Filigrane
        p.saveState()
        p.setFillColorRGB(0.9, 0.9, 0.9)
        p.setFont("Helvetica-Bold", 60)
        p.rotate(45)
        p.drawCentredString(width/2, -height/2, "BEST CONNECT")
        p.restoreState()

        p.showPage()
        p.save()
        return response

    @classmethod
    def get_statistics(cls):
        """Récupère les statistiques des paiements"""
        from subscriptions.models import Plan, Subscription
        import logging
        logger = logging.getLogger(__name__)

        # Récupérer tous les forfaits
        try:
            plans = Plan.objects.all()
            logger.info(f"Nombre de forfaits trouvés : {plans.count()}")
            
            # Créer les statistiques pour chaque forfait
            subscription_stats = []
            for plan in plans:
                # Compter les abonnements actifs
                active_subscriptions = Subscription.objects.filter(
                    plan=plan,
                    is_active=True
                ).count()

                # Calculer le montant total des paiements réussis
                total_amount = cls.objects.filter(
                    plan=plan,
                    status='SUCCESS'
                ).aggregate(total=models.Sum('amount'))['total'] or 0

                # Récupérer le dernier paiement réussi pour ce forfait
                last_payment = cls.objects.filter(
                    plan=plan,
                    status='SUCCESS'
                ).order_by('-created_at').first()

                subscription_stats.append({
                    'id': plan.id,
                    'name': plan.name,
                    'price': plan.price,
                    'count': active_subscriptions,
                    'total_amount': total_amount,
                    'payment_id': last_payment.id if last_payment and last_payment.status == 'SUCCESS' else None
                })
                logger.info(f"Forfait trouvé : {plan.name} (ID: {plan.id})")

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des forfaits : {str(e)}")
            subscription_stats = []

        # Si aucun forfait n'existe, créer un forfait par défaut
        if not subscription_stats:
            logger.info("Aucun forfait trouvé, création d'un forfait par défaut")
            try:
                default_plan = Plan.objects.create(
                    name="Forfait Test",
                    price=10000,
                    description="Forfait de test",
                    duration=30,
                    duration_unit='DAYS'
                )
                subscription_stats = [{
                    'id': default_plan.id,
                    'name': default_plan.name,
                    'price': default_plan.price,
                    'count': 0,
                    'total_amount': 0,
                    'payment_id': None
                }]
                logger.info(f"Forfait par défaut créé : {default_plan.name}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du forfait par défaut : {str(e)}")

        # Statistiques journalières des 7 derniers jours
        end_date = timezone.now()
        start_date = end_date - timedelta(days=6)
        
        # Créer une liste de dates pour les 7 derniers jours
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.date())
            current_date += timedelta(days=1)

        # Récupérer les statistiques des paiements
        try:
            daily_stats = cls.objects.filter(
                created_at__range=(start_date, end_date),
                status='SUCCESS'
            ).annotate(
                day=TruncDate('created_at')
            ).values('day').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('day')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques journalières : {str(e)}")
            daily_stats = []

        # Convertir en dictionnaire pour un accès facile
        daily_stats_dict = {stat['day']: stat for stat in daily_stats}

        # Créer une liste complète avec toutes les dates
        complete_daily_stats = []
        for date in date_list:
            if date in daily_stats_dict:
                stat = daily_stats_dict[date]
                complete_daily_stats.append({
                    'day': date,
                    'count': stat['count'],
                    'total_amount': float(stat['total_amount'] or 0)
                })
            else:
                complete_daily_stats.append({
                    'day': date,
                    'count': 0,
                    'total_amount': 0
                })

        # Calculer les totaux
        total_subscriptions = sum(stat['count'] for stat in subscription_stats)
        total_subscription_amount = sum(stat['total_amount'] or 0 for stat in subscription_stats)
        total_payments = sum(day['count'] for day in complete_daily_stats)
        total_amount = sum(day['total_amount'] for day in complete_daily_stats)

        logger.info(f"Totaux : {total_subscriptions} abonnements, {total_subscription_amount} Ar")

        return {
            'subscription_stats': subscription_stats,
            'daily_stats': complete_daily_stats,
            'total_subscriptions': total_subscriptions,
            'total_subscription_amount': total_subscription_amount,
            'total_payments': total_payments,
            'total_amount': total_amount
        }