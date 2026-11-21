from collections.abc import Mapping

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission


class Page(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RolePermission(BasePermission):
    role = None

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == self.role


class StudentOnly(RolePermission):
    role = "student"


class ManagerOnly(RolePermission):
    role = "manager"


class AdminOnly(RolePermission):
    role = "admin"


def require_role(user, *roles):
    if user.role not in roles:
        raise PermissionDenied("This action is unavailable for your role.")



def object_data(request):
    if not isinstance(request.data, Mapping):
        raise ValidationError({"detail": "Expected an object in the request body."})
    return request.data
