from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Feedback, FeedbackReply
from .serializers import FeedbackSerializer, FeedbackReplySerializer
from .tasks import send_feedback_confirmation_task, send_feedback_reply_task


class FeedbackCreateView(generics.CreateAPIView):
    """Authenticated users submit feedback."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = FeedbackSerializer

    def perform_create(self, serializer):
        feedback = serializer.save(user=self.request.user)
        send_feedback_confirmation_task.delay(feedback.id)


class FeedbackListView(generics.ListAPIView):
    """Authenticated users see their own feedback history."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = FeedbackSerializer
    search_fields = ['category', 'message']
    filterset_fields = ['category', 'is_resolved']
    ordering_fields = ['created_at', 'category']

    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user).prefetch_related('replies__user')


class AdminFeedbackView(generics.ListAPIView):
    """Admin-only view of all feedback with filter support."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = FeedbackSerializer
    search_fields = ['message', 'user__name', 'user__email', 'category']
    ordering_fields = ['created_at', 'category', 'is_resolved']

    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or user.is_admin):
            return Feedback.objects.none()
        qs = Feedback.objects.select_related('user', 'project').prefetch_related('replies__user').all()
        category  = self.request.query_params.get('category')
        resolved  = self.request.query_params.get('resolved')
        if category:
            qs = qs.filter(category=category)
        if resolved is not None:
            qs = qs.filter(is_resolved=resolved.lower() == 'true')
        return qs


class AdminFeedbackResolveView(APIView):
    """Mark feedback as resolved (admin only)."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if not (request.user.is_staff or request.user.is_admin):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            fb = Feedback.objects.prefetch_related('replies__user').get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        fb.is_resolved = True
        fb.save()
        return Response(FeedbackSerializer(fb).data)


class FeedbackReplyListCreateView(generics.ListCreateAPIView):
    """List replies on a feedback or create a new reply."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = FeedbackReplySerializer

    def get_queryset(self):
        return FeedbackReply.objects.filter(feedback_id=self.kwargs['feedback_pk']).select_related('user')

    def perform_create(self, serializer):
        feedback = get_object_or_404(Feedback, pk=self.kwargs['feedback_pk'])
        reply = serializer.save(feedback=feedback, user=self.request.user)
        if reply.user != feedback.user:
            send_feedback_reply_task.delay(reply.id)
