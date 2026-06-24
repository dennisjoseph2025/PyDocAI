from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Feedback
from ..serializers import FeedbackSerializer
from ..tasks import send_feedback_confirmation_task


class FeedbackCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        feedback = serializer.save(user=request.user)
        send_feedback_confirmation_task.delay(feedback.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeedbackListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Feedback.objects.filter(user=request.user).prefetch_related('replies__user')

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(category__icontains=search) |
                Q(message__icontains=search)
            )

        for field in ['category', 'is_resolved']:
            val = request.query_params.get(field)
            if val is not None:
                qs = qs.filter(**{field: val})

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'category', '-created_at', '-category']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        serializer = FeedbackSerializer(qs, many=True)
        return Response(serializer.data)


class AdminFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.is_staff or user.is_admin):
            return Response([])

        qs = Feedback.objects.select_related('user', 'project').prefetch_related('replies__user').all()

        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        resolved = request.query_params.get('resolved')
        if resolved is not None:
            qs = qs.filter(is_resolved=resolved.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(message__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(category__icontains=search)
            )

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'category', 'is_resolved', '-created_at', '-category', '-is_resolved']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        serializer = FeedbackSerializer(qs, many=True)
        return Response(serializer.data)


class AdminFeedbackResolveView(APIView):
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
