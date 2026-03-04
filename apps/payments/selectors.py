from typing import Optional

from django.db.models import QuerySet

from .models import Payment
from ..orders.models import Order


def get_payment_by_id(payment_id: int) -> Optional[Payment]:
    try:
        return Payment.objects.select_related('order', 'order__user').get(id=payment_id)
    except Payment.DoesNotExist:
        return None


def get_payment_by_order(order_id: int) -> Optional[Payment]:
    try:
        return Payment.objects.select_related('order', 'order__user').get(order_id=order_id)
    except Payment.DoesNotExist:
        return None


def get_payment_by_intent_id(stripe_payment_intent_id: str) -> Optional[Payment]:
    try:
        return Payment.objects.select_related('order', 'order__user').get(
            stripe_payment_intent_id=stripe_payment_intent_id
        )
    except Payment.DoesNotExist:
        return None


def get_user_payments(user, status: str = None) -> QuerySet[Payment]:
    queryset = Payment.objects.filter(
        order__user=user
    ).select_related('order').order_by('-created_at')

    if status:
        queryset = queryset.filter(status=status)
    return queryset


def get_payments_by_status(status: str) -> QuerySet[Payment]:
    return Payment.objects.filter(
        status=status
    ).select_related('order', 'order__user').order_by('-created_at')


def get_pending_payments_for_order(order: Order) -> QuerySet[Payment]:
    return Payment.objects.filter(
        order=order,
        status__in=[Payment.Status.PENDING, Payment.Status.PROCESSING]
    )


def get_successful_payments_count(user) -> int:
    return Payment.objects.filter(
        order__user=user,
        status=Payment.Status.SUCCEEDED
    ).count()


def get_payment_statistics(user) -> dict:
    from django.db.models import Sum, Count
    payments = Payment.objects.filter(order__user=user)
    status_counts = payments.values('status').annotate(count=Count('id'))
    total_spent = payments.filter(
        status=Payment.Status.SUCCEEDED
    ).aggregate(total=Sum('amount'))['total'] or 0
    result = {
        'total_payments': payments.count(),
        'total_spent': float(total_spent),
        'pending_count': 0,
        'processing_count': 0,
        'succeeded_count': 0,
        'failed_count': 0,
        'cancelled_count': 0,
        'refunded_count': 0,
    }

    for item in status_counts:
        key = f"{item['status']}_count"
        if key in result:
            result[key] = item['count']
    return result


def payment_exists_for_order(order_id: int) -> bool:
    return Payment.objects.filter(order_id=order_id).exists()


def is_order_paid(order_id: int) -> bool:
    return Payment.objects.filter(
        order_id=order_id,
        status=Payment.Status.SUCCEEDED
    ).exists()
