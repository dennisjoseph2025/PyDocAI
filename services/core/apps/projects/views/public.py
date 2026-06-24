from django.core.cache import cache
from django.db.models import Count, Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import PublicProjectPage

from ..models import Project
from ..serializers import PublicProjectListSerializer, PublicProjectSerializer
from ..throttles import PublicRateThrottle


class PublicProjectListView(APIView):
    permission_classes = []
    throttle_classes = [PublicRateThrottle]

    def get(self, request):
        qs = (Project.objects
              .filter(is_published=True, status='done')
              .select_related('user')
              .annotate(file_count=Count('files'))
              .order_by('-updated_at'))

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        paginator = PublicProjectPage()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = PublicProjectListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PublicProjectListSerializer(qs, many=True)
        return Response(serializer.data)


class PublicProjectDetailView(APIView):
    permission_classes = []
    throttle_classes = [PublicRateThrottle]

    def get(self, request, slug):
        cache_key = f'public_project_{slug}'
        data = cache.get(cache_key)
        if not data:
            try:
                project = (Project.objects
                           .filter(public_slug=slug, is_published=True)
                           .select_related('user')
                           .prefetch_related('files')
                           .get())
            except Project.DoesNotExist:
                return Response({"detail": "Not found."}, status=404)
            data = PublicProjectSerializer(project).data
            cache.set(cache_key, data, 300)
        return Response(data)
