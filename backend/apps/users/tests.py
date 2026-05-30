from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class UserAuthTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'username': 'testuser',
            'password': 'strongpassword123',
            'password2': 'strongpassword123'
        }

    @patch('apps.users.tasks.send_welcome_email_task.delay')
    def test_user_registration(self, mock_email_task):
        """Test successful user registration and token generation."""
        response = self.client.post('/api/users/register/', self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        mock_email_task.assert_called_once()

    def test_user_registration_password_mismatch(self):
        """Test registration fails if passwords do not match."""
        data = self.user_data.copy()
        data['password2'] = 'differentpassword'
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_login(self):
        """Test user login returns JWT tokens."""
        User.objects.create_user(email='login@example.com', name='Login', password='password123')
        response = self.client.post('/api/users/login/', {
            'email': 'login@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_get_profile_unauthenticated(self):
        """Ensure unauthenticated users cannot access profile."""
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_and_update_profile(self):
        """Test getting and updating the authenticated user's profile."""
        user = User.objects.create_user(email='profile@example.com', name='Old Name', password='pwd')
        self.client.force_authenticate(user=user)
        
        # Get profile
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Old Name')

        # Update profile
        response = self.client.patch('/api/users/profile/', {'name': 'New Name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.name, 'New Name')