from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import PasswordResetToken, User
from ..serializers import PasswordResetConfirmSerializer, PasswordResetRequestSerializer


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
            from ..tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(user.id, str(token.token))
        except User.DoesNotExist:
            pass
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
