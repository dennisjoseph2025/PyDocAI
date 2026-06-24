from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Feedback, FeedbackReply
from ..serializers import FeedbackReplySerializer
from ..tasks import send_feedback_reply_task


class FeedbackReplyListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, feedback_pk):
        qs = FeedbackReply.objects.filter(
            feedback_id=feedback_pk
        ).select_related('user')
        serializer = FeedbackReplySerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, feedback_pk):
        feedback = get_object_or_404(Feedback, pk=feedback_pk)
        serializer = FeedbackReplySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        reply = serializer.save(feedback=feedback, user=request.user)
        if reply.user != feedback.user:
            send_feedback_reply_task.delay(reply.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
