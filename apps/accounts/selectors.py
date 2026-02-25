from typing import Optional

from .models import CustomUser


def get_user_by_email(email: str) -> Optional[CustomUser]:
    """
    Get user by email
    Args:
        email: User's email
    Returns:
        CustomUser instance or None if not found
    """
    try:
        return CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None


def get_user_by_id(user_id: int) -> Optional[CustomUser]:
    """
    Get user by ID
    Args:
        user_id: User's ID
    Returns:
        CustomUser instance or None if not found
    """
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return None


def get_all_users():
    """
    Get all users
    Returns:
        QuerySet of all CustomUser instances
    """
    return CustomUser.objects.all()


def get_active_users():
    """
    Get all active users
    Returns:
        QuerySet of active CustomUser instances
    """
    return CustomUser.objects.filter(is_active=True)


def email_exists(email: str) -> bool:
    """
    Check if email already exists
    Args:
        email: Email to check
    Returns:
        True if email exists, False otherwise
    """
    return CustomUser.objects.filter(email=email).exists()


def get_staff_users():
    """
    Get all staff users
    Returns:
        QuerySet of staff CustomUser instances
    """
    return CustomUser.objects.filter(is_staff=True)
