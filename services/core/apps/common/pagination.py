from rest_framework.pagination import PageNumberPagination


class NoPagination(PageNumberPagination):
    page_size = None


class AdminUserPage(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class PublicProjectPage(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50
