from django.db import models

from apps.orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    currency = models.CharField(max_length=3, default='usd')
    failure_message = models.TextField(blank=True, null=True)
    idempotency_key = models.CharField(max_length=255, blank=True, null=True, unique=True)
    client_secret = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]

    def __str__(self) -> str:
        return f"Payment for Order #{self.order.id} - {self.get_status_display()} - {self.currency.upper()} {self.amount}"

    @property
    def is_successful(self) -> bool:
        return self.status == self.Status.SUCCEEDED

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING

    @property
    def is_failed(self) -> bool:
        return self.status == self.Status.FAILED

    @property
    def can_be_refunded(self) -> bool:
        return self.status == self.Status.SUCCEEDED
