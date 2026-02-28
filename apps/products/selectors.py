from .models import Category, Product, ProductImage


def get_all_categories():
    """
    Get all categories
    Returns:
        QuerySet of all Category instances
    """
    return Category.objects.all()


def get_category_by_slug(slug: str) -> Category:
    """
    Get category by slug
    Args:
        slug: Category slug
    Returns:
        Category instance or None if not found
    """
    try:
        return Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return None


def get_category_by_id(category_id: int) -> Category:
    """
    Get category by ID
    Args:
        category_id: Category ID
    Returns:
        Category instance or None if not found
    """
    try:
        return Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return None


def get_all_products():
    """
    Get all products
    Returns:
        QuerySet of all Product instances
    """
    return Product.objects.all()


def get_product_by_slug(slug: str) -> Product:
    """
    Get product by slug
    Args:
        slug: Product slug
    Returns:
        Product instance or None if not found
    """
    try:
        return Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return None


def get_product_images(product: Product):
    """
    Get all images for a product
    Args:
        product: Product instance
    Returns:
        QuerySet of ProductImage instances related to the product
    """
    return ProductImage.objects.filter(product=product)


def get_active_products():
    """
    Get all active products
    Returns:
        QuerySet of active Product instances
    """
    return Product.objects.filter(is_active=True)


def get_products_by_category(category: Category):
    """
    Get products by category
    Args:
        category: Category instance
    Returns:
        QuerySet of Product instances related to the category
    """
    return Product.objects.filter(category=category)


def get_image_by_id(image_id: int) -> ProductImage:
    """
    Get product image by ID
    Args:
        image_id: ProductImage ID
    Returns:
        ProductImage instance or None if not found
    """
    try:
        return ProductImage.objects.get(id=image_id)
    except ProductImage.DoesNotExist:
        return None
