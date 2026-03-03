from django.urls import path

from .views import (
    CheckoutView,
    OrderListView,
    OrderDetailView,
    CancelOrderView,
    AdminOrderListView,
    UpdateOrderStatusView,
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('admin/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:order_id>/status/', UpdateOrderStatusView.as_view(), name='update-order-status'),
]
