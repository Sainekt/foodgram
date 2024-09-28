from rest_framework import filters

from common.constants import (AUTHOR, IS_FAVORITED, IS_IN_SHOPPING_CART, NAME,
                              RECIPES, TAGS)


class IngredientSearchFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        name = request.query_params.get(NAME)
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
        tags = request.query_params.getlist(TAGS)
        author = request.query_params.getlist(AUTHOR)
        is_in_shopping_cart = request.query_params.get(
            IS_IN_SHOPPING_CART
        )
        is_favorited = request.query_params.get(
            IS_FAVORITED
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
                data[i][RECIPES] = data[i][RECIPES][:recipes_limit]
        else:
            data[RECIPES] = data[RECIPES][:recipes_limit]

        return data
