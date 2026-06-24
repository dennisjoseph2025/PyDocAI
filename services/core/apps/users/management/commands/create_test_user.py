from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a test user for API testing'

    def handle(self, *args, **options):
        user_model = get_user_model()

        # Delete existing test user if exists
        user_model.objects.filter(username='testuser').delete()

        # Create fresh user
        user = user_model.objects.create(
            username='testuser',
            email='test@example.com',
        )
        user.password = make_password('testpass123')
        user.save()

        self.stdout.write(self.style.SUCCESS('Test user created successfully!'))
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write('Password: testpass123')
