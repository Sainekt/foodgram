from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (
    Tag,
    Ingredient,
    IngredientsRecipes,
    Recipe,
    TagsRecipes,
    FavoriteRecipes,
    ShoppingCart,
)

admin.site.empty_value_display = 'Не задано'

User = get_user_model()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_editable = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_editable = ('name', 'measurement_unit')
    readonly_fields = ('id',)


@admin.register(IngredientsRecipes)
class IngredientsRecipes(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe')
    list_display_links = ('recipe',)
    search_fields = ('ingredient', 'recipe')
    list_editable = ('ingredient',)
    prefetch_related = ('recipe_ingredients',)


@admin.register(Recipe)
class Recipe(admin.ModelAdmin):
    list_display = (
        'id', 'image', 'name', 'text',
        'author', 'short_link'
    )

    search_fields = ('text', 'author__username', 'name__name')
    list_editable = ('text', 'author', 'name')


@admin.register(TagsRecipes)
class TagsRecipes(admin.ModelAdmin):
    list_display = ('id', 'tag', 'recipe')
    search_fields = ('tag', 'recipe')
    prefetch_related = ('recipe_tags',)


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = (
        'user', 'recipe'
    )
    search_fields = ('user__username', 'recipe')


@admin.register(FavoriteRecipes)
class FavoriteRecipes(admin.ModelAdmin):
    list_display = (
        'user', 'recipe'
    )
    search_fields = ('user__username', 'recipe')
