from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SubscriptionViewSet
from . import views

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/subscriptions/subscription/<int:subscription_id>/print/', 
         views.print_subscription_receipt, 
         name='print-subscription-receipt'),
] 