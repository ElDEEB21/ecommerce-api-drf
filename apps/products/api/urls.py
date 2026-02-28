from django.urls import path

from .views import (
    ProductListCreateView,
    ProductDetailView,
    CategoryListCreateView,
    CategoryDetailView,
    ProductImageUploadView,
    ProductImageDetailView,
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('<slug:slug>/images/', ProductImageUploadView.as_view(), name='product-image-upload'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('images/<int:pk>/', ProductImageDetailView.as_view(), name='product-image-detail'),
]
