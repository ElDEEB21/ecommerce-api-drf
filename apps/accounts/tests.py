from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from . import selectors
from .models import CustomUser
from .services import AuthService, UserService


class CustomUserModelTest(TestCase):
    """Test CustomUser model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_user(self):
        """Test creating a user"""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = CustomUser.objects.create_superuser(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str(self):
        """Test user string representation"""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])


class SelectorsTest(TestCase):
    """Test selector functions"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

    def test_get_user_by_email(self):
        """Test getting user by email"""
        user = selectors.get_user_by_email('test@example.com')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')

    def test_get_user_by_email_not_found(self):
        """Test getting non-existent user by email"""
        user = selectors.get_user_by_email('nonexistent@example.com')
        self.assertIsNone(user)

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        user = selectors.get_user_by_id(self.user.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

    def test_email_exists(self):
        """Test checking if email exists"""
        self.assertTrue(selectors.email_exists('test@example.com'))
        self.assertFalse(selectors.email_exists('nonexistent@example.com'))

    def test_get_all_users(self):
        """Test getting all users"""
        users = selectors.get_all_users()
        self.assertEqual(users.count(), 1)

    def test_get_active_users(self):
        """Test getting active users"""
        users = selectors.get_active_users()
        self.assertEqual(users.count(), 1)


class AuthServiceTest(TestCase):
    """Test AuthService"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register(self):
        """Test user registration"""
        user = AuthService.register(self.user_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        AuthService.register(self.user_data)
        with self.assertRaises(ValueError):
            AuthService.register(self.user_data)

    def test_authenticate(self):
        """Test user authentication"""
        AuthService.register(self.user_data)
        user = AuthService.authenticate(
            self.user_data['email'],
            self.user_data['password']
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.user_data['email'])

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password"""
        AuthService.register(self.user_data)
        user = AuthService.authenticate(
            self.user_data['email'],
            'WrongPassword'
        )
        self.assertIsNone(user)

    def test_get_tokens_for_user(self):
        """Test getting tokens for user"""
        user = AuthService.register(self.user_data)
        tokens = AuthService.get_tokens_for_user(user)
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)


class UserServiceTest(TestCase):
    """Test UserService"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

    def test_change_password(self):
        """Test changing password"""
        new_password = 'NewPassword123!'
        UserService.change_password(self.user, 'TestPassword123!', new_password)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_change_password_wrong_old_password(self):
        """Test change password with wrong old password"""
        with self.assertRaises(ValueError):
            UserService.change_password(self.user, 'WrongPassword', 'NewPassword123!')

    def test_update_profile(self):
        """Test updating user profile"""
        UserService.update_profile(
            self.user,
            first_name='Updated',
            last_name='Name'
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_get_user_data(self):
        """Test getting user data"""
        data = UserService.get_user_data(self.user)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)


class AuthAPITest(APITestCase):
    """Test authentication API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password2': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register_user(self):
        """Test user registration via API"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_register_user_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.user_data.copy()
        data['password2'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user(self):
        """Test user login via API"""
        # First register
        self.client.post(self.register_url, self.user_data, format='json')

        # Then login
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)

    def test_login_wrong_credentials(self):
        """Test login with wrong credentials"""
        # First register
        self.client.post(self.register_url, self.user_data, format='json')

        # Login with wrong password
        login_data = {
            'email': self.user_data['email'],
            'password': 'WrongPassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAPITest(APITestCase):
    """Test user API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        self.users_url = reverse('accounts:user-list-create')

    def test_list_users(self):
        """Test listing all users"""
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_user(self):
        """Test creating a user via API"""
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.users_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], data['email'])
