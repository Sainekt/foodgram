from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredienFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name='name', method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        value = value.lower()
        if queryset := queryset.filter(name__istartswith=value):
            return queryset
        return self.queryset.filter(name__icontains=value)


class RecipeFilterSet(filters.FilterSet):
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )
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
