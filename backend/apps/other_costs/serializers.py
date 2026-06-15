from rest_framework import serializers
from .models import OtherCost


class OtherCostSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OtherCost
        fields = ['id', 'date', 'category', 'amount', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
