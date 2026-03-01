from django.urls import path

from .views import (
    UserListCreateAPIView,
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    ChangePasswordView,
    CurrentUserView,
)

app_name = 'accounts'

urlpatterns = [
    path('users/', UserListCreateAPIView.as_view(), name='user-list-create'),  # Development only, remove in production
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
]
