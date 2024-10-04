from rest_framework.viewsets import ReadOnlyModelViewSet

from common.constants import REQUEST


class ListRetriveMixin(ReadOnlyModelViewSet):
    pagination_class = None


class GetUserMixin:
    def get_user_object(self):
        """return user model object or False"""
        if (not self.context.get(REQUEST)
                or not self.context[REQUEST].user.is_authenticated):
            return False
        return self.context[REQUEST].user
