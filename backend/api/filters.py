from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe

from common.constants import (NAME, RECIPES)


class IngredientSearchFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', method='filter_name')

    class Meta:
        model = Ingredient
        fields = [NAME]

    def filter_name(self, queryset, name, value):
        value = value.lower()
        if queryset := queryset.filter(name__istartswith=value):
            return queryset
        return self.queryset.filter(name__icontains=value)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not value or not self.request.user.is_authenticated:
            return queryset
        return queryset.filter(
            shopping_cart__user=self.request.user).distinct()

    def filter_is_favorited(self, queryset, name, value):
        if not value or not self.request.user.is_authenticated:
            return queryset
        return queryset.filter(
            favorite_recipes__user=self.request.user).distinct()


def recipe_limit(request, data: dict):
    limit = request.query_params.get('recipes_limit')
    if not limit or not limit.isdigit():
        return data
    limit = int(limit)
    if type(data) is list:
        for i in range(len(data)):
            data[i][RECIPES] = data[i][RECIPES][:limit]
    else:
        data[RECIPES] = data[RECIPES][:limit]

    return data
