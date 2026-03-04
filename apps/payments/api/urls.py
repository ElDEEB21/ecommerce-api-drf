from django.urls import path

from .views import (
    CreatePaymentIntentView,
    PaymentDetailView,
    PaymentByOrderView,
    PaymentListView,
    PaymentStatusView,
    CancelPaymentView,
    RefundPaymentView,
    SyncPaymentStatusView,
    PaymentStatisticsView,
    StripeWebhookView,
    PublishableKeyView,
)

app_name = 'payments'

urlpatterns = [
    path('', PaymentListView.as_view(), name='list'),
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-intent'),
    path('<int:payment_id>/', PaymentDetailView.as_view(), name='detail'),
    path('<int:payment_id>/status/', PaymentStatusView.as_view(), name='status'),
    path('order/<int:order_id>/', PaymentByOrderView.as_view(), name='by-order'),
    path('cancel/', CancelPaymentView.as_view(), name='cancel'),
    path('refund/', RefundPaymentView.as_view(), name='refund'),
    path('sync-status/', SyncPaymentStatusView.as_view(), name='sync-status'),
    path('statistics/', PaymentStatisticsView.as_view(), name='statistics'),
    path('config/', PublishableKeyView.as_view(), name='config'),
    path('webhook/', StripeWebhookView.as_view(), name='webhook'),
]
