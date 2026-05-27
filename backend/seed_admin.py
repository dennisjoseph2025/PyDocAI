import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from apps.users.models import User

email = 'admin@gmail.com'
if not User.objects.filter(email=email).exists():
    user = User.objects.create_superuser(
    email=email,
    name='Admin',
    username='admin',
    password='admin1234'
    )
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.is_verified = True
    user.save()
    print(f'Created admin user: {user.email}')
else:
    print(f'User with email {email} already exists.')