from rest_framework.permissions import OR, SAFE_METHODS, BasePermission


class UserOrReadOnlyBasePermissions(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and self.get_user_permissions(
                request, view, obj))
        )

    def get_user_permissions(self, request, view, obj):
        return False


class IsAuthorOrReadOnly(UserOrReadOnlyBasePermissions):
    def get_user_permissions(self, request, view, obj):
        return request.user == obj.author


class IsAdminOrReadOnly(UserOrReadOnlyBasePermissions):
    def get_user_permissions(self, request, view, obj):
        return request.user.is_staff


class IsUserOrReadOnly(UserOrReadOnlyBasePermissions):
    def get_user_permissions(self, request, view, obj):
        return request.user == obj


class IsAdminOrCurrentUserOrReadOnly(BasePermission):
    """for settings djoser permissions"""
    permissions_set = OR(IsUserOrReadOnly(), IsAdminOrReadOnly())

    def has_permission(self, request, view):
        return self.permissions_set.has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self.permissions_set.has_object_permission(request, view, obj)
