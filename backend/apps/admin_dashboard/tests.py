from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminDashboardTests(APITestCase):
    def setUp(self):
        self.standard_user = User.objects.create_user(
            email='user@test.com', name='User', password='pwd', role=User.Role.USER
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com', name='Admin', password='pwd'
        )

    def test_admin_stats_forbidden_for_standard_user(self):
        """Standard users should receive a 403 Forbidden on admin endpoints."""
        self.client.force_authenticate(user=self.standard_user)
        response = self.client.get('/api/admin-dashboard/stats/')
        self.assertEqual(response.status_code, 403)

    def test_admin_stats_allowed_for_admin(self):
        """Admins should be able to view platform statistics."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin-dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.data)
        self.assertIn('projects', response.data)
        self.assertEqual(response.data['users']['total'], 2) # The two we created in setUp