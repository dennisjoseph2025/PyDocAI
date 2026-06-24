import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestCommentListView:
    def test_public_published_project(self, api_client, published_project):
        url = reverse('comment_list', args=[published_project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'comments' in response.data
        assert 'has_next' in response.data

    def test_unpublished_requires_auth(self, api_client, project):
        url = reverse('comment_list', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unpublished_owner_can_view(self, api_client, project, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_list', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_non_owner_cannot_view_unpublished(self, api_client, project, other_user):
        api_client.force_authenticate(user=other_user)
        url = reverse('comment_list', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_not_found(self, api_client):
        url = reverse('comment_list', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_top_level_only(self, api_client, published_project, user):
        from apps.comments.models import Comment
        top = Comment.objects.create(project=published_project, user=user, content='Top')
        Comment.objects.create(project=published_project, user=user, parent=top, content='Reply')
        api_client.force_authenticate(user=user)
        url = reverse('comment_list', args=[published_project.id])
        response = api_client.get(url)
        assert len(response.data['comments']) == 1
        assert response.data['comments'][0]['content'] == 'Top'

    def test_pagination(self, api_client, published_project, user):
        from apps.comments.models import Comment
        for i in range(5):
            Comment.objects.create(project=published_project, user=user, content=f'C{i}')
        url = reverse('comment_list', args=[published_project.id])
        response = api_client.get(url + '?limit=2')
        assert len(response.data['comments']) == 2
        assert response.data['has_next'] is True


class TestCommentCreateView:
    def test_unauthenticated(self, api_client, published_project):
        url = reverse('comment_create', args=[published_project.id])
        response = api_client.post(url, {'content': 'Great!'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_comment(self, api_client, published_project, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_create', args=[published_project.id])
        response = api_client.post(url, {'content': 'Nice project!'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Nice project!'

    def test_create_reply(self, api_client, published_project, user, comment):
        api_client.force_authenticate(user=user)
        url = reverse('comment_create', args=[published_project.id])
        response = api_client.post(url, {'content': 'A reply', 'parent': str(comment.id)})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['parent'] == comment.id

    def test_project_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_create', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.post(url, {'content': 'Test'})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_data(self, api_client, published_project, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_create', args=[published_project.id])
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCommentDeleteView:
    def test_unauthenticated(self, api_client, comment):
        url = reverse('comment_delete', args=[comment.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_own_comment(self, api_client, comment, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_delete', args=[comment.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_delete_others_comment(self, api_client, comment, other_user):
        api_client.force_authenticate(user=other_user)
        url = reverse('comment_delete', args=[comment.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_sets_deleted(self, api_client, comment, user):
        api_client.force_authenticate(user=user)
        url = reverse('comment_delete', args=[comment.id])
        api_client.delete(url)
        comment.refresh_from_db()
        assert comment.content == '[deleted]'
