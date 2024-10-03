from rest_framework.permissions import SAFE_METHODS, BasePermission, OR


class IsAutentificateOrReadOnlyPermissions(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )


class IsAuthorOrReadOnly(IsAutentificateOrReadOnlyPermissions):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and request.user == obj.author)
        )


class IsAdminOrReadOnly(IsAutentificateOrReadOnlyPermissions):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_staff)
        )


class IsUserOrReadOnly(IsAutentificateOrReadOnlyPermissions):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and request.user == obj)
        )


class IsAdminOrCurrentUserOrReadOnly(BasePermission):
    """for settings djoser permissions"""
    permissions_set = OR(IsUserOrReadOnly(), IsAdminOrReadOnly())

    def has_permission(self, request, view):
        return self.permissions_set.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self.permissions_set.has_object_permission(request, view, obj)
