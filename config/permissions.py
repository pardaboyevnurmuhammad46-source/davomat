from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


class HasRole(BasePermission):
    roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.is_superuser or user.role in self.roles


class IsAdmin(HasRole):
    roles = (User.Role.ADMIN,)


class IsTeacher(HasRole):
    roles = (User.Role.TEACHER,)


class IsStudent(HasRole):
    roles = (User.Role.STUDENT,)


class IsStaff(HasRole):
    roles = (User.Role.ADMIN, User.Role.TEACHER)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_superuser or user.role == User.Role.ADMIN