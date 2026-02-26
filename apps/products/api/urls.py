from django.urls import path

from .views import (
    ProductListCreateView,
    ProductDetailView,
    CategoryListCreateView,
    CategoryDetailView,
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
]
