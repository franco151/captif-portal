from rest_framework import serializers
from .models import WiFiCredentials, Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'duration_days']

class WiFiCredentialsSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = WiFiCredentials
        fields = ['username', 'password', 'expires_at', 'qr_code']

    def get_qr_code(self, obj):
        return obj.get_qr_code_base64() 