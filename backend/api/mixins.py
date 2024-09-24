from rest_framework import viewsets, mixins


class ListRetriveMixin(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    pagination_class = None
