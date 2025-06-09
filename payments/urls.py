from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.create_payment, name='create_payment'),
    path('<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('<int:payment_id>/print/', views.print_receipt, name='print_receipt'),
    path('daily-receipts-pdf/<str:date>/', views.print_daily_receipts_pdf, name='daily_receipts_pdf'),
] 