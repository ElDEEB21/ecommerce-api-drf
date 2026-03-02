from django.core.exceptions import ValidationError
from django.db import transaction

from . import selectors
from .models import CartItem
from ..products.models import Product


class CartService:
    @staticmethod
    def get_or_create_cart(user):
        return selectors.get_user_cart(user)

    @staticmethod
    @transaction.atomic
    def add_product(user, product_id, quantity):
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValidationError("Product not found")

        if not product.is_active:
            raise ValidationError("Product is not available")

        if product.stock_quantity < quantity:
            raise ValidationError(f"Not enough stock. Available: {product.stock_quantity}")

        cart = CartService.get_or_create_cart(user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price_snapshot': product.price}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                raise ValidationError(
                    f"Not enough stock. Available: {product.stock_quantity}, Current in cart: {cart_item.quantity}")
            cart_item.quantity = new_quantity
            cart_item.save()
        return cart

    @staticmethod
    @transaction.atomic
    def update_item_quantity(user, item_id, quantity):
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative")

        cart = CartService.get_or_create_cart(user)

        try:
            cart_item = CartItem.objects.select_related('product').get(cart=cart, id=item_id)
        except CartItem.DoesNotExist:
            return None

        if quantity == 0:
            cart_item.delete()
            return None

        if cart_item.product.stock_quantity < quantity:
            raise ValidationError(f"Not enough stock. Available: {cart_item.product.stock_quantity}")

        cart_item.quantity = quantity
        cart_item.save()
        return cart_item

    @staticmethod
    def remove_item(user, item_id):
        cart = CartService.get_or_create_cart(user)
        try:
            cart_item = CartItem.objects.get(cart=cart, id=item_id)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False

    @staticmethod
    def clear_cart(user):
        cart = CartService.get_or_create_cart(user)
        CartItem.objects.filter(cart=cart).delete()

    @staticmethod
    def calculate_cart_total(cart):
        items = CartItem.objects.filter(cart=cart)
        total = sum(item.quantity * item.price_snapshot for item in items)
        return total
