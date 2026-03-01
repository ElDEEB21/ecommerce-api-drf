from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from . import selectors
from .models import CustomUser


class CookieService:
    """Service for handling JWT cookie operations"""

    @staticmethod
    def get_cookie_settings():
        """Returns JWT cookie settings from Django settings."""
        return getattr(settings, 'JWT_COOKIE_SETTINGS', {})

    @staticmethod
    def set_auth_cookies(response, tokens):
        """Sets access and refresh token cookies on the response."""
        cookie_settings = CookieService.get_cookie_settings()
        access_cookie_name = cookie_settings.get('ACCESS_TOKEN_COOKIE_NAME', 'access_token')
        refresh_cookie_name = cookie_settings.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        cookie_secure = cookie_settings.get('COOKIE_SECURE', False)
        cookie_httponly = cookie_settings.get('COOKIE_HTTPONLY', True)
        cookie_samesite = cookie_settings.get('COOKIE_SAMESITE', 'Lax')
        cookie_max_age = cookie_settings.get('COOKIE_MAX_AGE', 60 * 60 * 24 * 7)

        response.set_cookie(
            key=access_cookie_name,
            value=tokens['access'],
            max_age=300,
            secure=cookie_secure,
            httponly=cookie_httponly,
            samesite=cookie_samesite,
        )

        if 'refresh' in tokens:
            response.set_cookie(
                key=refresh_cookie_name,
                value=tokens['refresh'],
                max_age=cookie_max_age,
                secure=cookie_secure,
                httponly=cookie_httponly,
                samesite=cookie_samesite,
            )

        return response

    @staticmethod
    def delete_auth_cookies(response):
        """Deletes access and refresh token cookies from the response."""
        cookie_settings = CookieService.get_cookie_settings()
        refresh_cookie_name = cookie_settings.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        access_cookie_name = cookie_settings.get('ACCESS_TOKEN_COOKIE_NAME', 'access_token')
        cookie_samesite = cookie_settings.get('COOKIE_SAMESITE', 'Lax')
        response.delete_cookie(
            key=refresh_cookie_name,
            samesite=cookie_samesite
        )
        response.delete_cookie(
            key=access_cookie_name,
            samesite=cookie_samesite
        )

        return response

    @staticmethod
    def get_refresh_token_from_request(request):
        """
        Extracts refresh token from request.
        Tries cookies first (more secure), then falls back to request body.
        Returns tuple: (refresh_token, cookie_name)
        """
        cookie_settings = CookieService.get_cookie_settings()
        refresh_cookie_name = cookie_settings.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        refresh_token = request.COOKIES.get(refresh_cookie_name)
        if not refresh_token:
            refresh_token = request.data.get('refresh')
        return refresh_token, refresh_cookie_name


class AuthService:

    @staticmethod
    def register(user_data: dict):
        """
        Register a new user
        Args:
            user_data: Dictionary containing email, password, first_name, last_name
        Returns:
            CustomUser instance
        Raises:
            ValueError if email already exists
        """
        email = user_data.get('email')
        if not email:
            raise ValueError("Email is required")

        if CustomUser.objects.filter(email=email).exists():
            raise ValueError("Email already exists")

        password = user_data.get('password')
        if not password:
            raise ValueError("Password is required")

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )
        return user

    @staticmethod
    def logout(refresh_token: str):
        """
        Logout a user by blacklisting the refresh token
        Args:
            refresh_token: The refresh token string to blacklist
        Raises:
            ValueError if refresh token is invalid
        """
        try:
            token = RefreshToken(refresh_token)  # type: ignore
            token.blacklist()
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    @staticmethod
    def authenticate(email: str, password: str):
        """
        Authenticate a user by email and password
        Args:
            email: User's email
            password: User's password
        Returns:
            CustomUser instance if authenticated, None otherwise
        """
        try:
            user = selectors.get_user_by_email(email)
            if user and user.check_password(password):
                return user
        except Exception:
            pass
        return None

    @staticmethod
    def get_tokens_for_user(user):
        """
        Generate JWT tokens for a user
        Args:
            user: CustomUser instance
        Returns:
            Dictionary with access and refresh tokens
        """
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    @staticmethod
    def refresh_access_token(refresh_token: str):
        """
        Refresh access token using refresh token
        Args:
            refresh_token: The refresh token string
        Returns:
            Dictionary with new access token and optionally new refresh token
        Raises:
            Exception if refresh token is invalid or blacklisted
        """
        try:
            refresh = RefreshToken(refresh_token)  # type: ignore
            refresh.verify()
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        except Exception as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")


class UserService:

    @staticmethod
    def get_user_data(user):
        """
        Get user data as dictionary
        Args:
            user: CustomUser instance
        Returns:
            Dictionary with user data
        """
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
        }

    @staticmethod
    def change_password(user, old_password: str, new_password: str):
        """
        Change user password
        Args:
            user: CustomUser instance
            old_password: Current password
            new_password: New password
        Returns:
            Updated user instance
        Raises:
            ValueError if old password is incorrect
        """
        if not user.check_password(old_password):
            raise ValueError("Old password is incorrect")
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return user

    @staticmethod
    def update_profile(user, **kwargs):
        """
        Update user profile
        Args:
            user: CustomUser instance
            **kwargs: Fields to update
        Returns:
            Updated user instance
        """
        allowed_fields = ['first_name', 'last_name', 'email']
        for attr, value in kwargs.items():
            if value is None or attr not in allowed_fields:
                continue
            if hasattr(user, attr):
                setattr(user, attr, value)
        user.save()
        return user

    @staticmethod
    def get_all_users():
        """
        Get all users
        Returns:
            QuerySet of all users
        """
        return CustomUser.objects.all()

    @staticmethod
    def create_user(user_data: dict):
        """
        Create a new user
        Args:
            user_data: Dictionary containing user data
        Returns:
            CustomUser instance
        """
        password = user_data.get('password')
        user_dict = {k: v for k, v in user_data.items() if k != 'password'}
        user = CustomUser.objects.create(**user_dict)
        if password:
            user.set_password(password)
            user.save()
        return user
