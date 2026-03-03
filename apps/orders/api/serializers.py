from rest_framework import serializers

from apps.cart.api.serializers import ProductMiniSerializer
from ..models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True, required=True)
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_snapshot', 'item_total', 'created_at']
        read_only_fields = ['id', 'price_snapshot', 'created_at']

    def get_item_total(self, obj):
        return obj.quantity * obj.price_snapshot


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'created_at', 'updated_at', 'items', 'total_price']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return sum(item.quantity * item.price_snapshot for item in obj.items.all())
