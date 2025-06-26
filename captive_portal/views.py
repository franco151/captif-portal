from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
import json
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserSession
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg

@csrf_exempt
@api_view(['POST'])
def captive_portal_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({
                'message': 'Nom d\'utilisateur et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                # Vérifier si l'utilisateur a un abonnement actif
                subscription = user.subscription_set.filter(
                    is_active=True,
                    end_date__gt=timezone.now()
                ).first()

                if subscription:
                    # Générer un token de session
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        'message': 'Connexion réussie',
                        'redirectUrl': '/dashboard',
                        'token': str(refresh.access_token),
                        'user': {
                            'username': user.username,
                            'subscription': {
                                'plan': subscription.plan.name,
                                'end_date': subscription.end_date.strftime('%Y-%m-%d'),
                                'remaining_days': (subscription.end_date - timezone.now()).days
                            }
                        }
                    })
                else:
                    return Response({
                        'message': 'Aucun abonnement actif trouvé. Veuillez contacter l\'administrateur.'
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'message': 'Compte désactivé. Veuillez contacter l\'administrateur.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'message': 'Identifiants invalides'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except json.JSONDecodeError:
        return Response({
            'message': 'Données invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login(request):
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        mac_address = data.get('mac_address')  # Nouvelle ligne
        
        print(f"Tentative de connexion pour l'utilisateur: {username}")  # Debug log
        print(f"Données reçues: {data}")  # Debug log
        
        if not username or not password:
            return Response(
                {'error': 'Veuillez fournir un nom d\'utilisateur et un mot de passe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            print(f"Échec de l'authentification pour l'utilisateur: {username}")  # Debug log
            return Response(
                {'error': 'Identifiants invalides'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            print(f"Compte désactivé pour l'utilisateur: {username}")  # Debug log
            return Response(
                {'error': 'Compte désactivé'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier si l'utilisateur a un abonnement actif
        subscription = user.subscription_set.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).first()
        
        if not subscription:
            print(f"Aucun abonnement actif pour l'utilisateur: {username}")  # Debug log
            return Response(
                {'error': 'Aucun abonnement actif trouvé. Veuillez contacter l\'administrateur.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # NOUVELLE LOGIQUE : Vérifier si l'utilisateur a déjà une session active sur un autre appareil
        if mac_address and UserSession.has_active_session_on_different_device(user, mac_address):
            return Response(
                {'error': 'DEVICE_ALREADY_USED', 'message': 'Ce ticket est déjà utilisé par un autre appareil. Impossible de se connecter sur le même ticket depuis plusieurs appareils. Je vous conseille d\'acheter un autre ticket, mon ami, pas cher le ticket !'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Vérifier si c'est le même appareil qui se reconnecte
        if mac_address:
            existing_session = UserSession.check_mac_address_usage(user, mac_address)
            if existing_session:
                # Récupérer la session existante
                session = UserSession.get_active_session_by_mac(user, mac_address)
                if session:
                    return Response({
                        'access_token': str(RefreshToken.for_user(user).access_token),
                        'session_id': session.id,
                        'message': 'Session existante récupérée',
                        'user': {
                            'username': user.username,
                            'email': user.email,
                            'subscription': {
                                'plan': subscription.plan.name,
                                'end_date': subscription.end_date.strftime('%Y-%m-%d'),
                                'remaining_days': (subscription.end_date - timezone.now()).days
                            }
                        }
                    })
        
        # Créer une nouvelle session avec l'adresse MAC
        session = UserSession.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            mac_address=mac_address  # Nouvelle ligne
        )
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        print(f"Connexion réussie pour l'utilisateur: {username}")  # Debug log
        
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'session_id': session.id,
            'user': {
                'username': user.username,
                'email': user.email,
                'subscription': {
                    'plan': subscription.plan.name,
                    'end_date': subscription.end_date.strftime('%Y-%m-%d'),
                    'remaining_days': (subscription.end_date - timezone.now()).days
                }
            }
        })
        
    except Exception as e:
        print(f"Erreur lors de la connexion: {str(e)}")  # Debug log
        return Response(
            {'error': f'Une erreur est survenue: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    session_id = request.data.get('session_id')
    if session_id:
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            session.end_session()
            return Response({'message': 'Déconnexion réussie'})
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Session non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    return Response(
        {'error': 'ID de session requis'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_status(request):
    session_id = request.query_params.get('session_id')
    if session_id:
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            
            # Récupérer les informations de subscription
            from subscriptions.models import Subscription
            subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            subscription_info = None
            if subscription:
                subscription_info = {
                    'start_date': subscription.start_date,
                    'end_date': subscription.end_date,
                    'plan_name': subscription.plan.name,
                    'is_expired': subscription.end_date.date() < timezone.now().date()
                }
            
            return Response({
                'is_active': session.is_active,
                'remaining_time': session.get_remaining_time(),
                'mac_address': session.mac_address,
                'ip_address': session.ip_address,
                'start_time': session.start_time,
                'subscription': subscription_info
            })
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Session non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    return Response(
        {'error': 'ID de session requis'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_network_activity(request):
    """Enregistre une activité réseau"""
    session_id = request.data.get('session_id')
    activity_type = request.data.get('activity_type')
    
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        
        activity = NetworkActivity.objects.create(
            session=session,
            activity_type=activity_type,
            ip_address=request.data.get('ip_address', session.ip_address),
            mac_address=request.data.get('mac_address', session.mac_address),
            bytes_uploaded=request.data.get('bytes_uploaded', 0),
            bytes_downloaded=request.data.get('bytes_downloaded', 0),
            bandwidth_usage=request.data.get('bandwidth_usage', 0),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data=request.data.get('additional_data', {})
        )
        
        return Response({'status': 'success', 'activity_id': activity.id})
    except UserSession.DoesNotExist:
        return Response({'error': 'Session non trouvée'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analytics(request):
    """Récupère les analytics de l'utilisateur"""
    user = request.user
    
    # Sessions de l'utilisateur
    sessions = UserSession.objects.filter(user=user).order_by('-start_time')[:10]
    
    # Activités récentes
    recent_activities = NetworkActivity.objects.filter(
        session__user=user
    ).order_by('-timestamp')[:20]
    
    # Statistiques
    total_data = NetworkActivity.objects.filter(
        session__user=user
    ).aggregate(
        total_up=Sum('bytes_uploaded'),
        total_down=Sum('bytes_downloaded'),
        avg_bandwidth=Avg('bandwidth_usage')
    )
    
    # Appareils utilisés
    devices = DeviceFingerprint.objects.filter(user=user)
    
    return Response({
        'sessions': [{
            'id': s.id,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'ip_address': s.ip_address,
            'mac_address': s.mac_address,
            'is_active': s.is_active
        } for s in sessions],
        'recent_activities': [{
            'type': a.activity_type,
            'timestamp': a.timestamp,
            'data_transfer': a.data_transfer_mb,
            'bandwidth': a.bandwidth_usage
        } for a in recent_activities],
        'statistics': {
            'total_uploaded_mb': (total_data['total_up'] or 0) / (1024 * 1024),
            'total_downloaded_mb': (total_data['total_down'] or 0) / (1024 * 1024),
            'average_bandwidth': total_data['avg_bandwidth'] or 0
        },
        'devices': [{
            'name': d.device_name,
            'type': d.device_type,
            'os': d.operating_system,
            'last_seen': d.last_seen,
            'is_trusted': d.is_trusted
        } for d in devices]
    })