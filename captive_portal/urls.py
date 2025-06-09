from django.urls import path
from . import views

app_name = 'captive_portal'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('check-status/', views.check_status, name='check_status'),
] 