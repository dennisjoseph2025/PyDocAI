from django.db.models import Count, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import AdminUserPage
from ..models import User
from ..serializers import AdminUserSerializer, UserSerializer


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({"results": [], "stats": {}})

        qs = User.objects.annotate(
            project_count=Count('projects'),
            published_count=Count('projects', filter=Q(projects__is_published=True)),
        ).all()

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(name__icontains=search) |
                Q(username__icontains=search)
            )

        filterset_fields = ['role', 'is_verified', 'is_active']
        for field in filterset_fields:
            val = request.query_params.get(field)
            if val is not None:
                qs = qs.filter(**{field: val})

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'email', 'name', '-created_at', '-email', '-name']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        paginator = AdminUserPage()
        page = paginator.paginate_queryset(qs, request)
        serializer = AdminUserSerializer(page, many=True) if page is not None else AdminUserSerializer(qs, many=True)

        if page is not None:
            return paginator.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})
