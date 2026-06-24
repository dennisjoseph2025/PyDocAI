from .stats import AdminStatsView
from .users import AdminUserListView, AdminUserDetailView, AdminUserDeleteView, AdminUserBlockView
from .projects import AdminProjectListView, AdminUserProjectsView, AdminProjectDetailView

__all__ = [
    'AdminStatsView',
    'AdminUserListView',
    'AdminUserDetailView',
    'AdminUserDeleteView',
    'AdminUserBlockView',
    'AdminProjectListView',
    'AdminUserProjectsView',
    'AdminProjectDetailView',
]
