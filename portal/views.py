from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import hashlib
import base64
from Crypto.Cipher import AES
from django.conf import settings
from .models import Payment, WiFiCredentials, Plan
from .serializers import PaymentSerializer, PlanSerializer, WiFiCredentialsSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class WiFiCredentialsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WiFiCredentials.objects.all()
    serializer_class = WiFiCredentialsSerializer
    permission_classes = [permissions.IsAdminUser]

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
                'credentials': WiFiCredentialsSerializer(credentials).data
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
            'credentials': WiFiCredentialsSerializer(payment.wificredentials).data if hasattr(payment, 'wificredentials') else None
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