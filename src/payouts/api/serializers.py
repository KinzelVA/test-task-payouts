from decimal import Decimal
from rest_framework import serializers
from payouts.models import PayoutRequest


class PayoutRequestCreateSerializer(serializers.Serializer):
    client_reference = serializers.CharField(max_length=64)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.CharField(max_length=3)
    destination = serializers.CharField(max_length=256)

    def validate_currency(self, value: str) -> str:
        value = value.upper()
        if len(value) != 3:
            raise serializers.ValidationError("Currency must be 3-letter ISO-like code.")
        return value


class PayoutRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        fields = [
            "id",
            "client_reference",
            "amount",
            "currency",
            "destination",
            "status",
            "failure_reason",
            "created_at",
            "updated_at",
            "processed_at",
        ]
        read_only_fields = fields
