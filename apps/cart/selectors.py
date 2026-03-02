from .models import Cart, CartItem


def get_user_cart(user):
    """Get or create a cart for the user"""
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


def get_user_cart_with_items(user):
    """Get user's cart with items and product details"""
    cart = get_user_cart(user)
    items = CartItem.objects.filter(cart=cart).select_related('product')
    return cart, items
