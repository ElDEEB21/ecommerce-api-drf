from django.core.cache import cache

from . import selectors
from .models import Product


def _invalidate_product_caches(product_slug=None):
    """
    Clear all product-related caches.
    Called after any product create/update/delete.
    """
    cache.delete_pattern("*product_list*")
    if product_slug:
        cache.delete(f"product_detail:{product_slug}")


def _invalidate_category_caches(category_slug=None):
    """Clear all category-related caches."""
    cache.delete_pattern("*category_list*")
    if category_slug:
        cache.delete(f"category_detail:{category_slug}")


class ProductService:

    @staticmethod
    def create_product(product_data: dict) -> Product:
        """
        Create a new product
        Args:
            product_data: Dictionary containing name, slug, description, price, stock_quantity, is_active, category_id
        Returns:
            Product instance
        Raises:
            ValueError if category does not exist
        """
        category_id = product_data.get('category_id')
        category = selectors.get_category_by_id(category_id)
        if not category:
            raise ValueError("Category does not exist")

        product = Product.objects.create(
            name=product_data.get('name'),
            slug=product_data.get('slug'),
            description=product_data.get('description', ''),
            price=product_data.get('price', 0.00),
            stock_quantity=product_data.get('stock_quantity', 0),
            is_active=product_data.get('is_active', True),
            category=category
        )
        _invalidate_product_caches()
        _invalidate_category_caches(category.slug)
        return product

    @staticmethod
    def update_product(product_data: dict) -> Product:
        """
        Update an existing product
        Args:
            product_data: Dictionary containing id, name, slug, description, price, stock_quantity, is_active, category_id
        Returns:
            Updated Product instance
        Raises:
            ValueError if product or category does not exist
        """
        product_id = product_data.get('id')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValueError("Product does not exist")

        old_slug = product.slug

        if 'category_id' in product_data:
            category_id = product_data.get('category_id')
            category = selectors.get_category_by_id(category_id)
            if not category:
                raise ValueError("Category does not exist")
            product.category = category

        product.name = product_data.get('name', product.name)
        product.slug = product_data.get('slug', product.slug)
        product.description = product_data.get('description', product.description)
        product.price = product_data.get('price', product.price)
        product.stock_quantity = product_data.get('stock_quantity', product.stock_quantity)
        product.is_active = product_data.get('is_active', product.is_active)

        product.save()
        _invalidate_product_caches(old_slug)
        if product.slug != old_slug:
            _invalidate_product_caches(product.slug)
        return product

    @staticmethod
    def delete_product(product_data: dict) -> Product:
        """
        Delete an existing product
        Args:
            product_data: Dictionary containing id
        Returns:
            Deleted Product instance
        Raises:
            ValueError if product does not exist
        """
        product_id = product_data.get('id')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValueError("Product does not exist")

        slug = product.slug
        product.delete()
        _invalidate_product_caches(slug)
        return product

    def add_image_to_product(product: Product, image_url: str) -> Product:
        """
        Add an image to a product
        Args:
            product: Product instance
            image_url: URL of the image to add
        Returns:
            Updated Product instance with the new image
        """
        product.images.create(image_url=image_url)
        _invalidate_product_caches(product.slug)
        return product

class InventoryService:

    @staticmethod
    def check_stock(product: Product, quantity: int) -> bool:
        """
        Check if the requested quantity of a product is in stock
        Args:
            product: Product instance
            quantity: Quantity to check
        Returns:
            True if the requested quantity is in stock, False otherwise
        """
        return product.stock_quantity >= quantity

    @staticmethod
    def decrease_stock(product: Product, quantity: int) -> Product:
        """
        Decrease the stock quantity of a product
        Args:
            product: Product instance
            quantity: Quantity to decrease
        Returns:
            Updated Product instance with decreased stock quantity
        Raises:
            ValueError if the requested quantity is greater than the available stock
        """
        if not InventoryService.check_stock(product, quantity):
            raise ValueError("Insufficient stock for the requested quantity")

        product.stock_quantity -= quantity
        product.save()
        _invalidate_product_caches(product.slug)
        return product

    @staticmethod
    def increase_stock(product: Product, quantity: int) -> Product:
        """
        Increase the stock quantity of a product
        Args:
            product: Product instance
            quantity: Quantity to increase
        Returns:
            Updated Product instance with increased stock quantity
        """
        product.stock_quantity += quantity
        product.save()
        _invalidate_product_caches(product.slug)
        return product
