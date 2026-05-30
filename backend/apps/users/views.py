from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .github import exchange_code_for_token, get_github_user
from .models import User,PasswordResetToken
from .serializers import RegisterSerializer,LoginSerializer,UserSerializer,ChangePasswordSerializer, GithubAuthSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
import requests
from django.conf import settings
from .email_utils import send_welcome_email, send_password_reset_email


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


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserSerializer
    search_fields = ['email', 'name', 'username']
    filterset_fields = ['role', 'is_verified', 'is_active']
    ordering_fields = ['created_at', 'email', 'name']

    def get_serializer_class(self):
        if self.request.user.is_admin:
            from .serializers import AdminUserSerializer
            return AdminUserSerializer
        return UserSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            from django.db.models import Count
            return User.objects.annotate(project_count=Count('projects')).all()
        return User.objects.none()
    
    
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

        # Keep the token fresh and ensure is_verified
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
        
        
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.save()
            tokens = get_tokens(user)
            # Send welcome email asynchronously via Celery
            from .tasks import send_welcome_email_task
            send_welcome_email_task.delay(user.id)
            return Response({
                'user':   UserSerializer(user).data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.create(user=user)
            from .tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(user.id, str(token.token))
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        # Always return 200 to prevent email enumeration
        return Response({'detail': 'If that email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        try:
            user  = User.objects.get(email=data['email'])
            token = PasswordResetToken.objects.get(token=data['token'], user=user)
        except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        if not token.is_valid():
            return Response({'detail': 'Token has expired or already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
        user.save()
        token.used = True
        token.save()
        return Response({'detail': 'Password reset successfully.'})        