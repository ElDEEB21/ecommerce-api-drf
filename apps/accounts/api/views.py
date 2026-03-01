from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)
from .. import selectors
from ..services import AuthService, UserService, CookieService


class UserListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        users = selectors.get_all_users()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = UserService.create_user(serializer.validated_data)
                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = AuthService.register(serializer.validated_data)
                tokens = AuthService.get_tokens_for_user(user)
                user_data = UserSerializer(user).data
                use_cookies = request.query_params.get('use_cookies', 'false').lower() == 'true'
                response_data = {'user': user_data}
                if use_cookies:
                    response = Response(response_data, status=status.HTTP_201_CREATED)
                    response = CookieService.set_auth_cookies(response, tokens)
                    return response
                else:
                    response_data['tokens'] = tokens
                    return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            use_cookies = request.query_params.get('use_cookies', 'false').lower() == 'true'
            try:
                user = AuthService.authenticate(email=email, password=password)
                if user:
                    if not user.is_active:
                        return Response(
                            {"detail": "Account is disabled"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    tokens = AuthService.get_tokens_for_user(user)
                    user_data = UserSerializer(user).data
                    response_data = {'user': user_data}
                    if use_cookies:
                        response = Response(response_data, status=status.HTTP_200_OK)
                        response = CookieService.set_auth_cookies(response, tokens)
                        return response
                    else:
                        response_data['tokens'] = tokens
                        return Response(response_data, status=status.HTTP_200_OK)
                return Response(
                    {"detail": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            refresh_token, refresh_cookie_name = CookieService.get_refresh_token_from_request(request)
            use_cookies = request.query_params.get('use_cookies', 'false').lower() == 'true'
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tokens = AuthService.refresh_access_token(refresh_token)
            if use_cookies or request.COOKIES.get(refresh_cookie_name):
                response = Response(
                    {"detail": "Token refreshed successfully"},
                    status=status.HTTP_200_OK
                )
                response = CookieService.set_auth_cookies(response, tokens)
                return response
            else:
                return Response(tokens, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token, _ = CookieService.get_refresh_token_from_request(request)
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            AuthService.logout(refresh_token)
            response = Response(
                {
                    "detail": "Logged out successfully",
                    "security_info": {
                        "refresh_token": "blacklisted and cannot be reused",
                        "access_token": "will expire naturally in ~5 minutes",
                        "cookies": "deleted (if cookie-based auth was used)"
                    }
                },
                status=status.HTTP_200_OK
            )
            response = CookieService.delete_auth_cookies(response)
            return response
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            try:
                UserService.change_password(user, old_password, new_password)
                return Response(
                    {"detail": "Password changed successfully"},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            data = UserService.get_user_data(user)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_user = UserService.update_profile(user, **serializer.validated_data)
                return Response(UserSerializer(updated_user).data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
