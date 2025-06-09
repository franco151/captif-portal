from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'description', 'duration_hours', 'price', 'is_active')

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        write_only=True,
        source='plan'
    )

    class Meta:
        model = Subscription
        fields = ('id', 'user', 'plan', 'plan_id', 'start_date', 'end_date', 'status', 'created_at')
        read_only_fields = ('id', 'user', 'start_date', 'end_date', 'status', 'created_at') 