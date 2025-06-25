from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
import hashlib
import uuid  # Ajout manquant
from .models import Payment, SMSTransaction  # Ajout de SMSTransaction
from .serializers import PaymentSerializer
from portal.models import WiFiCredentials
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt  # Ajout manquant
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from subscriptions.models import Plan
from weasyprint import HTML
import tempfile
import os
from django.db.models.functions import TruncDate
from datetime import datetime
from django.db import models
from django.db.models import Count, Sum

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            # Décryptage du numéro de transaction
            encrypted_number = request.data.get('transaction_number')
            transaction_hash = request.data.get('transaction_number_hash')
            
            # Vérification du hash
            if hashlib.sha256(encrypted_number.encode()).hexdigest() != transaction_hash:
                return Response(
                    {'error': 'Hash de transaction invalide'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Création du paiement
            payment_data = {
                'plan': request.data.get('plan'),
                'amount': request.data.get('amount'),
                'transaction_number': encrypted_number,
                'transaction_hash': transaction_hash,
                'phone_number': request.data.get('phone_number'),
                'status': 'success'  # Dans un cas réel, vérifier le paiement
            }
            
            serializer = self.get_serializer(data=payment_data)
            serializer.is_valid(raise_exception=True)
            payment = serializer.save()

            # Création des identifiants WiFi
            credentials = WiFiCredentials.objects.create(
                payment=payment,
                expires_at=timezone.now() + timedelta(days=payment.plan.duration_days)
            )

            # Envoi des identifiants par SMS (à implémenter)
            self.send_credentials_sms(payment.phone_number, credentials)

            return Response({
                'payment': serializer.data,
                'credentials': credentials.username
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        payment = self.get_object()
        return Response({
            'status': payment.status,
            'credentials': payment.wificredentials.username if hasattr(payment, 'wificredentials') else None
        })

    def send_credentials_sms(self, phone_number, credentials):
        """
        Méthode pour envoyer les identifiants par SMS
        À implémenter avec un service SMS (Twilio, etc.)
        """
        message = f"""
        Vos identifiants BestConnect :
        Username: {credentials.username}
        Password: {credentials.password}
        Valables jusqu'au: {credentials.expires_at.strftime('%d/%m/%Y')}
        """
        # TODO: Implémenter l'envoi SMS
        print(f"SMS à envoyer à {phone_number}: {message}")

@staff_member_required
def print_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return payment.generate_receipt_pdf()

@login_required
def payment_list(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_list.html', {'payments': payments})

@login_required
def create_payment(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan')
        payment_method = request.POST.get('payment_method')
        phone_number = request.POST.get('phone_number')
        
        plan = get_object_or_404(Plan, id=plan_id)
        
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            payment_method=payment_method,
            phone_number=phone_number
        )
        
        messages.success(request, 'Paiement créé avec succès.')
        return redirect('payments:payment_detail', payment_id=payment.id)
    
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'payments/create_payment.html', {'plans': plans})

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payments/payment_detail.html', {'payment': payment})

@staff_member_required
def daily_receipts_redirect_view(request):
    """Vue de redirection pour les reçus quotidiens"""
    from django.shortcuts import redirect
    from datetime import date
    
    # Récupérer la date depuis les paramètres GET ou utiliser aujourd'hui
    date_param = request.GET.get('date')
    if date_param:
        return redirect('payments:daily_receipts_pdf', date=date_param)
    else:
        today = date.today().strftime('%Y-%m-%d')
        return redirect('payments:daily_receipts_pdf', date=today)

@staff_member_required
def print_daily_receipts_pdf(request, date):
    try:
        # Convertir la date string en objet date
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Date invalide", status=400)

    # Filtrer les paiements pour la date cible
    payments = Payment.objects.filter(
        created_at__date=target_date,
        status='SUCCESS' # Afficher uniquement les paiements réussis
    ).order_by('created_at')

    # Calculer le total pour cette date
    total_amount = payments.aggregate(total=models.Sum('amount'))['total'] or 0
    total_payments_count = payments.count()
    
    # Calculer l'effectif par mode de paiement
    payment_method_counts = payments.values('payment_method').annotate(count=Count('id'))

    # Contexte pour le template
    context = {
        'date': target_date,
        'payments': payments,
        'total_amount': total_amount,
        'total_payments_count': total_payments_count,
        'payment_method_counts': payment_method_counts, # Ajouter les statistiques par mode de paiement
        'generation_datetime': timezone.now() # Ajouter la date et l'heure de génération
    }

    # Rendre le template HTML
    html_string = render_to_string('payments/daily_receipts_pdf.html', context)

    # Générer le PDF avec WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reçus_paiement_{target_date.strftime('%Y-%m-%d')}.pdf"'
    html.write_pdf(response)

    return response


# Ajouter ces nouvelles vues API

@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_sms_payment(request):
    """Initier un paiement SMS - appelé depuis React"""
    try:
        plan_id = request.data.get('plan_id')
        phone_number = request.data.get('phone_number')
        
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        
        # Créer une transaction SMS en attente
        sms_transaction = SMSTransaction.objects.create(
            phone_number=phone_number,
            amount=plan.price,
            plan=plan,
            reference=f"REF{uuid.uuid4().hex[:8].upper()}",
            operator_message="En attente de paiement",
            status='PENDING'
        )
        
        return Response({
            'success': True,
            'transaction_id': sms_transaction.id,
            'reference': sms_transaction.reference,
            'amount': sms_transaction.amount,
            'ussd_code': f"*182*1*1*{sms_transaction.amount}*{sms_transaction.reference}#",
            'instructions': f"Composez *182*1*1*{sms_transaction.amount}*{sms_transaction.reference}# sur votre téléphone"
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_payment_status(request, transaction_id):
    """Vérifier le statut d'une transaction - polling depuis React"""
    try:
        transaction = get_object_or_404(SMSTransaction, id=transaction_id)
        
        if transaction.is_expired():
            transaction.status = 'EXPIRED'
            transaction.save()
            
        response_data = {
            'status': transaction.status,
            'reference': transaction.reference
        }
        
        # Si confirmé, retourner les credentials WiFi
        if transaction.status == 'CONFIRMED' and transaction.payment:
            credentials = transaction.payment.wificredentials
            response_data.update({
                'wifi_credentials': {
                    'username': credentials.username,
                    'password': credentials.password,
                    'qr_code': credentials.get_qr_code_base64(),
                    'expires_at': credentials.expires_at.isoformat()
                }
            })
            
        return Response(response_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@csrf_exempt
def process_sms_webhook(request):
    """Webhook pour traiter les SMS de confirmation de l'opérateur"""
    try:
        # Données du SMS reçu par le modem
        sms_data = request.data
        reference = sms_data.get('reference')
        phone_number = sms_data.get('phone_number')
        amount = sms_data.get('amount')
        
        # Trouver la transaction correspondante
        transaction = SMSTransaction.objects.get(
            reference=reference,
            phone_number=phone_number,
            status='PENDING'
        )
        
        if not transaction.is_expired() and float(amount) == float(transaction.amount):
            # Créer le paiement
            payment = Payment.objects.create(
                user_id=1,  # Utilisateur anonyme ou système
                plan=transaction.plan,
                amount=transaction.amount,
                payment_method='MOBILE_MONEY',
                phone_number=transaction.phone_number,
                status='SUCCESS'
            )
            
            # Générer les credentials WiFi
            credentials = WiFiCredentials.objects.create(
                payment=payment,
                expires_at=timezone.now() + timedelta(days=transaction.plan.get_duration_in_days())
            )
            
            # Mettre à jour la transaction
            transaction.status = 'CONFIRMED'
            transaction.payment = payment
            transaction.save()
            
            return Response({'success': True})
        else:
            transaction.status = 'FAILED'
            transaction.save()
            return Response({'error': 'Transaction invalide'}, status=400)
            
    except Exception as e:
        return Response({'error': str(e)}, status=400)