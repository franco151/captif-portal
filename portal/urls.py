from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, WiFiCredentialsViewSet

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'wificredentials', WiFiCredentialsViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 