import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Order, OrderItem
from ..cart.models import Cart
from ..products.models import Product

logger = logging.getLogger(__name__)


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

        cart_items = list(cart.items.select_related('product').all())
        if not cart_items:
            raise ValidationError("Cart is empty")

        for cart_item in cart_items:
            product = Product.objects.select_for_update().get(id=cart_item.product_id)
            if not product.is_active:
                raise ValidationError(f"Product '{product.name}' is no longer available")
            if product.stock_quantity < cart_item.quantity:
                raise ValidationError(
                    f"Not enough stock for {product.name}. "
                    f"Available: {product.stock_quantity}, Requested: {cart_item.quantity}"
                )

        total_amount = sum(
            cart_item.quantity * cart_item.price_snapshot for cart_item in cart_items
        )

        order = Order.objects.create(
            user=cart.user,
            total_amount=total_amount,
            shipping_address=shipping_address or ""
        )

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price_snapshot=cart_item.price_snapshot
            )
            Product.objects.filter(id=cart_item.product_id).update(
                stock_quantity=F('stock_quantity') - cart_item.quantity
            )

        cart.items.all().delete()
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order):
        if order.status not in [Order.Status.PENDING, Order.Status.PROCESSING]:
            raise ValidationError(
                f"Only pending or processing orders can be cancelled. "
                f"Current status: {order.status}"
            )

        from ..payments.models import Payment
        payment = Payment.objects.filter(
            order=order,
            status__in=[Payment.Status.PENDING, Payment.Status.PROCESSING]
        ).first()
        if payment:
            import stripe
            try:
                stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
                payment.status = Payment.Status.CANCELLED
                payment.save(update_fields=['status', 'updated_at'])
                logger.info(f"Cancelled payment {payment.id} along with order {order.id}")
            except Exception as e:
                logger.warning(f"Could not cancel payment {payment.id} for order {order.id}: {e}")

        order.status = Order.Status.CANCELLED
        order.save()

        for item in order.items.select_related('product').all():
            Product.objects.filter(id=item.product_id).update(
                stock_quantity=F('stock_quantity') + item.quantity
            )

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

        for item in cart.items.select_related('product').all():
            if not item.product.is_active:
                raise ValidationError(f"Product '{item.product.name}' is no longer available")
            if item.product.stock_quantity < item.quantity:
                raise ValidationError(f"Not enough stock for {item.product.name}")

    @staticmethod
    @transaction.atomic
    def process_checkout(order_id):
        order = Order.objects.select_for_update().get(id=order_id)

        if order.status != Order.Status.PENDING:
            raise ValidationError("Only pending orders can be checked out")

        order.status = Order.Status.PROCESSING
        order.save()
        return order
