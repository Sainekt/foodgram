# from rest_framework import filters
from django_filters import rest_framework as filters
from recipes.models import Ingredient

from common.constants import (AUTHOR, IS_FAVORITED, IS_IN_SHOPPING_CART, NAME,
                              RECIPES, TAGS)


class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        if not value:
            return queryset
        queryset = queryset.filter(name__istartswith=value)
        if not queryset.exists():
            queryset = self.queryset.filter(name__icontains=value)
        return queryset


class RecipeFilter(filters.FilterSet):
    ...
    search_param = TAGS
    def get_search_terms(self, request):
        return request.query_params.getlist(TAGS)

    def filter_queryset(self, request, queryset, view):
        terms = super().get_search_terms(request=request)
        print(terms)
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


class RecipeLimitFiler(filters.FilterSet):
    ...

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
