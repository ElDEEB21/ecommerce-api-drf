from decimal import Decimal

from rest_framework import serializers

from apps.orders.models import Order
from ..models import Payment


class OrderSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'created_at']
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    can_be_refunded = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'stripe_payment_intent_id', 'status', 'status_display',
            'amount', 'currency', 'failure_message', 'is_successful', 'is_pending',
            'is_failed', 'can_be_refunded', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PaymentStatusSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_successful = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'status', 'status_display', 'is_successful']
        read_only_fields = fields


class CreatePaymentIntentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True, min_value=1)
    currency = serializers.CharField(required=False, max_length=3, default='usd')
    idempotency_key = serializers.CharField(required=False, max_length=255, allow_blank=True)

    def validate_currency(self, value: str) -> str:
        if value and len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter ISO code.")
        return value.lower() if value else 'usd'

    def validate_order_id(self, value: int) -> int:
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Order with ID {value} does not exist.")
        return value


class PaymentIntentResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer(read_only=True)
    client_secret = serializers.CharField(read_only=True)
    publishable_key = serializers.CharField(read_only=True)


class CancelPaymentSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(required=True, min_value=1)

    def validate_payment_id(self, value: int) -> int:
        if not Payment.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Payment with ID {value} does not exist.")
        return value


class RefundPaymentSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(required=True, min_value=1)
    amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    reason = serializers.ChoiceField(
        required=False,
        choices=[('duplicate', 'Duplicate'), ('fraudulent', 'Fraudulent'),
                 ('requested_by_customer', 'Customer request')]
    )

    def validate_payment_id(self, value: int) -> int:
        try:
            payment = Payment.objects.get(id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError(f"Payment with ID {value} does not exist.")
        if not payment.can_be_refunded:
            raise serializers.ValidationError(f"Payment cannot be refunded. Status: {payment.status}")
        return value


class SyncPaymentStatusSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField(required=True, max_length=255)

    def validate_payment_intent_id(self, value: str) -> str:
        if not value.startswith('pi_'):
            raise serializers.ValidationError("Invalid PaymentIntent ID format. Must start with 'pi_'.")
        return value


class PaymentStatisticsSerializer(serializers.Serializer):
    total_payments = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    processing_count = serializers.IntegerField(read_only=True)
    succeeded_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    cancelled_count = serializers.IntegerField(read_only=True)
    refunded_count = serializers.IntegerField(read_only=True)
