from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse, Http404
from django.conf import settings
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch, mm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from io import BytesIO
import qrcode
from PIL import Image as PILImage

# Get an instance of a logger
logger = logging.getLogger(__name__)

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    # Permettre l'accès public aux plans pour le portail captif
    permission_classes = [permissions.AllowAny]
    
    # Limiter aux opérations de lecture seule pour les utilisateurs non authentifiés
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        plan_id = request.data.get('plan_id')
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {"error": "Forfait non trouvé ou inactif."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Vérifier si l'utilisateur a déjà un abonnement actif
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status='active',
            end_date__gt=timezone.now()
        ).first()

        if active_subscription:
            return Response(
                {"error": "Vous avez déjà un abonnement actif."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer le nouvel abonnement
        start_date = timezone.now()
        end_date = start_date + timedelta(hours=plan.duration_hours)

        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def active(self, request):
        subscription = Subscription.objects.filter(
            user=request.user,
            status='active',
            end_date__gt=timezone.now()
        ).first()

        if not subscription:
            return Response(
                {"error": "Aucun abonnement actif trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

def print_subscription_receipt(request, object_id):
    logger.debug(f"Received object_id: {object_id}")
    try:
        subscription = get_object_or_404(Subscription, id=object_id)
        
        # Créer le PDF en mémoire
        buffer = BytesIO()
        
        # Créer le document PDF avec une taille adaptée aux petites imprimantes (80mm de large)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(80*mm, 200*mm),  # 80mm de large, hauteur variable
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=12,
            spaceAfter=6,
            alignment=1,  # Center
            textColor=colors.white,
            backColor=colors.Color(0.255, 0.463, 0.565)  # #417690
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=9,
            spaceAfter=3,
            spaceBefore=6,
            textColor=colors.white,
            backColor=colors.Color(0.255, 0.463, 0.565),
            leftIndent=2*mm,
            rightIndent=2*mm
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=2,
            leftIndent=2*mm,
            rightIndent=2*mm
        )
        
        # Contenu du PDF
        story = []
        
        # En-tête
        story.append(Paragraph("BestConnect", title_style))
        story.append(Paragraph("Reçu d'inscription", title_style))
        story.append(Spacer(1, 6))
        
        # Informations utilisateur
        story.append(Paragraph("Informations utilisateur", section_style))
        story.append(Paragraph(f"<b>Nom d'utilisateur:</b> {subscription.user.username}", normal_style))
        story.append(Paragraph(f"<b>Mot de passe:</b> {subscription.user.plain_password or 'Non renseigné'}", normal_style))
        story.append(Paragraph(f"<b>Email:</b> {subscription.user.email or 'Non renseigné'}", normal_style))
        story.append(Paragraph(f"<b>Téléphone:</b> {subscription.user.phone_number or 'Non renseigné'}", normal_style))
        story.append(Paragraph(f"<b>Adresse:</b> {subscription.user.address or 'Non renseigné'}", normal_style))
        
        # Détails de l'abonnement
        story.append(Paragraph("Détails de l'abonnement", section_style))
        story.append(Paragraph(f"<b>Forfait:</b> {subscription.plan.name}", normal_style))
        story.append(Paragraph(f"<b>Prix:</b> {subscription.plan.price:,.0f} Ar", normal_style))
        story.append(Paragraph(f"<b>Date d'inscription:</b> {subscription.start_date.strftime('%d/%m/%Y')}", normal_style))
        story.append(Paragraph(f"<b>Date d'expiration:</b> {subscription.end_date.strftime('%d/%m/%Y')}", normal_style))
        
        # Informations de paiement
        story.append(Paragraph("Informations de paiement", section_style))
        story.append(Paragraph(f"<b>Méthode:</b> Espèces", normal_style))
        story.append(Paragraph(f"<b>Numéro de téléphone:</b> {subscription.user.phone_number}", normal_style))
        story.append(Paragraph(f"<b>Date de paiement:</b> {subscription.start_date.strftime('%d/%m/%Y %H:%M')}", normal_style))
        
        from datetime import datetime
        story.append(Paragraph(f"<b>Document généré le:</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
        
        story.append(Spacer(1, 10))
        
        # Générer le QR code
        qr_data = f"Nom d'utilisateur: {subscription.user.username}\nMot de passe: {subscription.user.plain_password or 'Non renseigné'}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image QR en mémoire
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Ajouter le QR code au PDF
        qr_image = Image(qr_buffer, width=30*mm, height=30*mm)
        qr_table = Table([[qr_image]], colWidths=[70*mm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(qr_table)
        
        story.append(Spacer(1, 10))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            alignment=1,  # Center
            textColor=colors.grey
        )
        
        story.append(Paragraph("<b>Merci de votre confiance</b>", footer_style))
        story.append(Paragraph("BestConnect - Votre partenaire de confiance", footer_style))
        story.append(Paragraph("Pour toute assistance: 034 72 497 15", footer_style))
        
        # Construire le PDF
        doc.build(story)
        
        # Préparer la réponse
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu_abonnement_{subscription.id}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de l'impression du reçu: {e}")
        raise Http404("Reçu non trouvé")