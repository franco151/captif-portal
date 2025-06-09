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
        
        # Créer une nouvelle session
        session = UserSession.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
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
            return Response({
                'is_active': session.is_active,
                'remaining_time': session.get_remaining_time()
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