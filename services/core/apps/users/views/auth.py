import requests
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..github import exchange_code_for_token, get_github_user
from ..models import User
from ..serializers import (
    GithubAuthSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.save()
            tokens = get_tokens(user)
            from ..tasks import send_welcome_email_task
            send_welcome_email_task.delay(user.id)
            return Response({
                'user':   UserSerializer(user).data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.validated_data['user']
            tokens = get_tokens(user)
            return Response({
                'user':   UserSerializer(user).data,
                'tokens': tokens,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
            return Response({'detail': 'Logged out successfully'})
        except KeyError:
            return Response({'detail': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


class GithubAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GithubAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']

        try:
            github_token = exchange_code_for_token(code)
        except requests.RequestException:
            return Response(
                {'detail': 'Failed to reach GitHub. Try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not github_token:
            return Response(
                {'detail': 'Invalid or expired OAuth code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            github_user = get_github_user(github_token)
        except requests.RequestException:
            return Response(
                {'detail': 'Failed to fetch GitHub profile.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        email = github_user.get('email')
        if not email:
            return Response(
                {'detail': 'Your GitHub account has no verified public email.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name':        github_user.get('name') or github_user.get('login', ''),
                'username':    github_user.get('login'),
                'is_verified': True,
            },
        )

        update_fields = ['github_token']
        user.github_token = github_token
        if not user.is_verified:
            user.is_verified = True
            update_fields.append('is_verified')
        user.save(update_fields=update_fields)

        tokens = get_tokens(user)
        return Response(
            {
                'user':    UserSerializer(user).data,
                'tokens':  tokens,
                'created': created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
