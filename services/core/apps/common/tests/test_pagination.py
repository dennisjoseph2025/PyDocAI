from apps.common.pagination import AdminUserPage, NoPagination, PublicProjectPage


class TestNoPagination:
    def test_page_size_none(self):
        paginator = NoPagination()
        assert paginator.page_size is None


class TestAdminUserPage:
    def test_page_size(self):
        paginator = AdminUserPage()
        assert paginator.page_size == 50

    def test_page_size_query_param(self):
        paginator = AdminUserPage()
        assert paginator.page_size_query_param == 'page_size'

    def test_max_page_size(self):
        paginator = AdminUserPage()
        assert paginator.max_page_size == 200


class TestPublicProjectPage:
    def test_page_size(self):
        paginator = PublicProjectPage()
        assert paginator.page_size == 12

    def test_page_size_query_param(self):
        paginator = PublicProjectPage()
        assert paginator.page_size_query_param == 'page_size'

    def test_max_page_size(self):
        paginator = PublicProjectPage()
        assert paginator.max_page_size == 50
