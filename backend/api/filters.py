from rest_framework import filters
from django.db import models
from functools import reduce
import operator


class CustomSearchFilter(filters.SearchFilter):
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
