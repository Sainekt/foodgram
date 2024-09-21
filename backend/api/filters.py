from rest_framework import filters
from django.db.models import Count
from django.db.models.query import QuerySet
from django.db import models
from functools import reduce
import operator


class IngredientSearchFilter(filters.SearchFilter):
    search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field), queryset)
            for search_field in search_fields
        ]

        base = queryset
        conditions = (
            reduce(
                operator.or_,
                # сделал фильтрацию не чувствительной к регистру.
                (models.Q(**{orm_lookup: term.lower()})
                    for orm_lookup in orm_lookups
                 )
            ) for term in search_terms
        )
        queryset = queryset.filter(reduce(operator.and_, conditions))

        if self.must_call_distinct(queryset, search_fields):
            queryset = queryset.filter(pk=models.OuterRef('pk'))
            queryset = base.filter(models.Exists(queryset))
        return queryset


class RecipeFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags')
        author = request.query_params.getlist('author')
        is_in_shopping_cart = request.query_params.getlist(
            'is_in_shopping_cart'
        )
        is_favorited = request.query_params.getlist(
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
                shopping_cart__in=is_in_shopping_cart).distinct()
        if is_favorited:
            queryset = queryset.filter(
                favorite_recipes__in=is_favorited).distinct()
        return queryset


class RecipeLimitFiler(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        recipes_limit = request.query_params.get('recipes_limit', None)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise ValueError('recipes_limit must be integer')

        if recipes_limit and type(queryset) is QuerySet:
            queryset = queryset.annotate(
                recipe_count=Count('subscriber__recipes')).filter(
                    recipe_count__lte=recipes_limit
            )
        else:
            self.filter_serializer_data(recipes_limit, queryset)
        return queryset

    def filter_serializer_data(self, recipes_limit, data):
        filter_recipes = data['recipes'][:recipes_limit]
        data['recipes'] = filter_recipes
        return data
