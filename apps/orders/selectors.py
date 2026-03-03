from .models import Order, OrderItem


def get_user_orders(user):
    """Returns all orders for a given user."""
    return Order.objects.filter(user=user)


def get_order_by_id(order_id):
    """Returns an order by its ID."""
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None


def get_order_items(order):
    """Returns all items for a given order."""
    return OrderItem.objects.filter(order=order)


def get_total_order_price(order):
    """Calculates the total price of an order."""
    order_items = get_order_items(order)
    total_price = sum(item.product.price * item.quantity for item in order_items)
    return total_price
