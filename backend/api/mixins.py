from rest_framework import viewsets

from common.constants import REQUEST


class ListRetriveMixin(viewsets.ReadOnlyModelViewSet):
    pagination_class = None


class GetUserMixin:
    def get_user_object(self):
        """return user model object or False"""
        if (not self.context.get(REQUEST)
                or not self.context[REQUEST].user.is_authenticated):
            return False
        return self.context[REQUEST].user
