from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAdminUser

from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CategoryDetailSerializer,
)
from .. import selectors
from ..services import ProductService


class ProductListCreateView(ListCreateAPIView):
    queryset = selectors.get_all_products()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'category__slug', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        product_data = serializer.validated_data
        product = ProductService.create_product(product_data)
        serializer.instance = product


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    queryset = selectors.get_all_products()
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_update(self, serializer):
        product_data = serializer.validated_data
        product_data['id'] = self.get_object().id
        product = ProductService.update_product(product_data)
        serializer.instance = product


class CategoryListCreateView(ListCreateAPIView):
    queryset = selectors.get_all_categories()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = selectors.get_all_categories()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategoryDetailSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]
