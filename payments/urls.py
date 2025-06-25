from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet)

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.create_payment, name='create_payment'),
    path('<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('<int:payment_id>/print/', views.print_receipt, name='print_receipt'),
    path('daily-receipts/<str:date>/', views.print_daily_receipts_pdf, name='daily_receipts_pdf'),
    path('daily-receipts-redirect/', views.daily_receipts_redirect_view, name='daily_receipts_redirect'),
    
    # Nouvelles API pour SMS
    path('api/initiate-sms-payment/', views.initiate_sms_payment, name='initiate_sms_payment'),
    path('api/check-payment-status/<int:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('api/process-sms-webhook/', views.process_sms_webhook, name='process_sms_webhook'),
    
    path('api/', include(router.urls)),
]