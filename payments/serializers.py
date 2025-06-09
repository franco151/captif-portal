from rest_framework import serializers
from .models import Payment
from portal.serializers import PlanSerializer, WiFiCredentialsSerializer

class PaymentSerializer(serializers.ModelSerializer):
    credentials = WiFiCredentialsSerializer(read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'plan', 'plan_details', 'amount', 'transaction_number',
            'transaction_hash', 'phone_number', 'status', 'created_at',
            'credentials'
        ]
        read_only_fields = ['transaction_hash', 'status', 'created_at'] 