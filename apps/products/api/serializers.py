from rest_framework import serializers

from ..models import Product, Category, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'required': True},
            'slug': {'required': True}
        }


class CategoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price']


class CategoryDetailSerializer(serializers.ModelSerializer):
    products = CategoryProductSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'products']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'is_primary']
        extra_kwargs = {
            'id': {'read_only': True},
            'product': {'required': True},
            'image_url': {'required': True},
            'is_primary': {'required': False, 'default': False}
        }


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'price',
            'stock_quantity',
            'is_active',
            'category',
            'category_id',
            'images',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'name': {'required': True},
            'slug': {'required': True},
            'price': {'required': True},
            'stock_quantity': {'required': True},
            'is_active': {'required': False, 'default': True},
            'category_id': {'required': True}
        }


