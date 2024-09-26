from rest_framework.pagination import PageNumberPagination


class RecipesPagination(PageNumberPagination):
    page_size_query_param = 'limit'

    def paginate_queryset(self, queryset, request, view=None):
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size and page_size.isdigit() and int(page_size) > 0:
            self.page_size = int(page_size)
        return super().paginate_queryset(queryset, request, view)
