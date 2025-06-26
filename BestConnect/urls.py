from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/captive-portal/', include('captive_portal.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),  # AJOUTER CETTE LIGNE
    path('payments/', include('payments.urls')),
    # ... autres URLs existantes ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)