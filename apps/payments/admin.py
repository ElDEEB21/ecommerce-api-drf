from django.contrib import admin
from django.utils.html import format_html

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order_link',
        'colored_status',
        'amount_display',
        'currency',
        'stripe_payment_intent_id_short',
        'created_at',
    ]
    list_filter = [
        'status',
        'currency',
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'order__id',
        'stripe_payment_intent_id',
        'order__user__email',
        'idempotency_key',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'order',
                'status',
                'amount',
                'currency',
            ),
        }),
        ('Stripe Details', {
            'fields': (
                'stripe_payment_intent_id',
                'idempotency_key',
                'client_secret',
            ),
        }),
        ('Error Information', {
            'fields': (
                'failure_message',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    readonly_fields = [
        'stripe_payment_intent_id',
        'idempotency_key',
        'client_secret',
        'created_at',
        'updated_at',
        'failure_message',
    ]

    def has_add_permission(self, request):
        return False

    def order_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)

    order_link.short_description = 'Order'
    order_link.admin_order_field = 'order__id'

    def colored_status(self, obj):
        colors = {
            'pending': '#FFA500',  # Orange
            'processing': '#007BFF',  # Blue
            'succeeded': '#28A745',  # Green
            'failed': '#DC3545',  # Red
            'cancelled': '#6C757D',  # Gray
            'refunded': '#17A2B8',  # Cyan
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    colored_status.short_description = 'Status'
    colored_status.admin_order_field = 'status'

    def amount_display(self, obj):
        currency_symbols = {
            'usd': '$',
            'eur': '€',
            'gbp': '£',
            'jpy': '¥',
        }
        symbol = currency_symbols.get(obj.currency.lower(), obj.currency.upper())
        return f"{symbol}{obj.amount}"

    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'

    def stripe_payment_intent_id_short(self, obj):
        if obj.stripe_payment_intent_id:
            return f"{obj.stripe_payment_intent_id[:20]}..."
        return '-'

    stripe_payment_intent_id_short.short_description = 'Stripe ID'
