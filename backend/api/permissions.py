from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrCurrentUserOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (
            (request.method in SAFE_METHODS)
            or (request.user.is_authenticated and request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        return (
            (request.method in SAFE_METHODS)
            or (request.user.is_authenticated and request.user.is_staff)
            or (request.user.is_authenticated and obj == request.user)
        )


class IsAuthorOrAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user == obj.author
            or request.user.is_staff
        )


class BaseReadOnlyPermissions(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsAuthorOrReadOnly(BaseReadOnlyPermissions):
    def has_object_permission(self, request, view, obj):
        return (
            (request.method in SAFE_METHODS)
            or (request.user.is_authenticated and obj == request.user)
        )


class IsAdminOrReadOnly(BaseReadOnlyPermissions):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_staff
        )
