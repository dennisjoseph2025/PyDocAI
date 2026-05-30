from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.projects.models import Project

User = get_user_model()

class ProjectTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', name='User1', password='pwd')
        self.user2 = User.objects.create_user(email='user2@example.com', name='User2', password='pwd')
        
        self.project1 = Project.objects.create(
            user=self.user1,
            name='Project 1',
            status=Project.Status.DONE
        )
        self.project2 = Project.objects.create(
            user=self.user2,
            name='Project 2',
            status=Project.Status.PENDING
        )

    def test_list_projects(self):
        """Users should only see their own projects."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stats']['total'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Project 1')

    def test_get_project_detail(self):
        """User can get details of their own project."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/projects/{self.project1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Project 1')

    def test_cannot_access_others_project(self):
        """User cannot access another user's project."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/projects/{self.project2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_project(self):
        """User can delete their own project."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f'/api/projects/{self.project1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Project.objects.filter(id=self.project1.id).exists())