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
        # Utiliser 'object_id' pour récupérer l'abonnement
        subscription = get_object_or_404(Subscription, id=object_id)

        html_content = render_to_string('admin/subscriptions/subscription/receipt.html', {
            'subscription': subscription,
            'user': subscription.user,
            'plan': subscription.plan,
        })

        response = HttpResponse(html_content)
        response['Content-Type'] = 'text/html'
        return response
    except Exception as e:
        logger.error(f"Erreur lors de l'impression du reçu: {e}")
        raise Http404("Reçu non trouvé")