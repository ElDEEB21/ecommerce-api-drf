from django.core.exceptions import ValidationError
from django.db import transaction

from . import selectors
from .models import Order, OrderItem
from ..cart.models import Cart
from ..products.models import Product


class OrderService:
    ALLOWED_TRANSITIONS = {
        Order.Status.PENDING: [Order.Status.PROCESSING, Order.Status.CANCELLED],
        Order.Status.PROCESSING: [Order.Status.SHIPPED, Order.Status.CANCELLED],
        Order.Status.SHIPPED: [Order.Status.DELIVERED],
        Order.Status.DELIVERED: [],
        Order.Status.CANCELLED: [],
    }

    @staticmethod
    def validate_status_transition(order, new_status):
        current_status = order.status
        allowed_statuses = OrderService.ALLOWED_TRANSITIONS.get(current_status, [])

        if new_status not in allowed_statuses:
            raise ValidationError(
                f"Cannot change order status from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {', '.join(allowed_statuses) if allowed_statuses else 'none'}"
            )

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user_id, shipping_address=None):
        try:
            cart = Cart.objects.select_for_update().get(user_id=user_id)
        except Cart.DoesNotExist:
            raise ValidationError("Cart not found")
        if not cart.items.exists():
            raise ValidationError("Cart is empty")

        total_amount = sum(cart_item.quantity * cart_item.product.price for cart_item in cart.items.all())
        order = Order.objects.create(
            user=cart.user,
            total_amount=total_amount,
            shipping_address=shipping_address or ""
        )

        for cart_item in cart.items.all():
            product = Product.objects.get(id=cart_item.product_id)
            if product.stock_quantity < cart_item.quantity:
                raise ValidationError(f"Not enough stock for {product.name}")
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                price_snapshot=product.price
            )
            product.stock_quantity -= cart_item.quantity
            product.save()

        cart.items.all().delete()
        return order

    @staticmethod
    def cancel_order(order):
        if order.status not in [Order.Status.PENDING, Order.Status.PROCESSING]:
            raise ValidationError(
                f"Only pending or processing orders can be cancelled. "
                f"Current status: {order.status}"
            )

        order.status = Order.Status.CANCELLED
        order.save()
        for item in order.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()

    @staticmethod
    def update_order_status(order, new_status):
        valid_statuses = [choice[0] for choice in Order.Status.choices]
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid order status: {new_status}")
        OrderService.validate_status_transition(order, new_status)
        order.status = new_status
        order.save()


class CheckoutService:

    @staticmethod
    def validate_cart_before_checkout(cart):
        if not cart.items.exists():
            raise ValidationError("Cart is empty")

        for item in cart.items.all():
            product = Product.objects.get(id=item.product_id)
            if product.stock_quantity < item.quantity:
                raise ValidationError(f"Not enough stock for {product.name}")

    @staticmethod
    def process_checkout(order_id):
        order = selectors.get_order_by_id(order_id)
        if not order:
            raise ValidationError("Order not found")

        if order.status != Order.Status.PENDING:
            raise ValidationError("Only pending orders can be checked out")

        order.status = Order.Status.PROCESSING
        order.save()
        return order
