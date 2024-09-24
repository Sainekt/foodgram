from rest_framework import filters


class IngredientSearchFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get('name')
        if not name:
            return queryset
        name = name.lower()
        queryset_filter = queryset.filter(
            name__istartswith=name).distinct()
        if not queryset_filter:
            queryset_filter = queryset.filter(
                name__icontains=name
            ).distinct()
        return queryset_filter


class RecipeFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags')
        author = request.query_params.getlist('author')
        is_in_shopping_cart = request.query_params.get(
            'is_in_shopping_cart'
        )
        is_favorited = request.query_params.get(
            'is_favorited'
        )
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if author:
            queryset = queryset.filter(author__id__in=author).distinct()
        if not request.user.is_authenticated:
            return queryset
        if is_in_shopping_cart:
            queryset = queryset.filter(
                shopping_cart__user=request.user).distinct()
        if is_favorited:
            queryset = queryset.filter(
                favorite_recipes__user=request.user).distinct()
        return queryset


class RecipeLimitFiler(filters.BaseFilterBackend):

    def filter_queryset(self, request, data: dict, view):
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise ValueError('recipes_limit must be integer')

        if type(data) is list:
            for i in range(len(data)):
                data[i]['recipes'] = data[i]['recipes'][:recipes_limit]
        else:
            data['recipes'] = data['recipes'][:recipes_limit]

        return data
