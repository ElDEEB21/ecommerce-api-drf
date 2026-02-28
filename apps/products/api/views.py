from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CategoryDetailSerializer,
    ProductImageSerializer,
)
from .. import selectors
from ..models import ProductImage
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


class ProductImageUploadView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, slug):
        product = selectors.get_product_by_slug(slug)
        if not product:
            return Response({"detail": "Product not found."}, status=404)
        image_url = request.data.get('image_url')
        if not image_url:
            return Response({"detail": "image_url is required."}, status=400)
        try:
            product = ProductService.add_image_to_product(product, image_url)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(ProductSerializer(product).data, status=201)


class ProductImageDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    lookup_field = 'pk'

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]


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
