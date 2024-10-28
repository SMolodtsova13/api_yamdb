from rest_framework.permissions import (
    SAFE_METHODS, BasePermission, IsAuthenticatedOrReadOnly
)


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin)


class IsAdminOrReadOnly(IsAdmin):

    def has_permission(self, request, view):
        return (super().has_permission(request, view)
                or request.method in SAFE_METHODS)


class IsAuthorOrAdminOrModerator(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user == obj.author
                or request.user.is_moderator
                or request.user.is_admin)
