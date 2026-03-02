from django.urls import path

from .views import (
    CartView,
    AddCartItemView,
    UpdateRemoveCartItemView,
    ClearCartView,
)

urlpatterns = [
    path('', CartView.as_view(), name='cart'),
    path('items/', AddCartItemView.as_view(), name='add-cart-item'),
    path('items/<int:item_id>/', UpdateRemoveCartItemView.as_view(), name='update-remove-cart-item'),
    path('clear/', ClearCartView.as_view(), name='clear-cart'),
]
