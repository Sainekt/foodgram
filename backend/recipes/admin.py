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


class TagsRecipesInline(admin.TabularInline):
    model = TagsRecipes
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_editable = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_display_links = ('name',)


@admin.register(IngredientsRecipes)
class IngredientsRecipesAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe')
    list_display_links = ('recipe',)
    search_fields = ('ingredient__name', 'recipe__name')
    list_editable = ('ingredient',)
    prefetch_related = ('recipe_ingredients',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author__username', 'favorite_count')
    search_fields = ('author__username', 'name',)
    list_display_links = ('id', 'name')
    list_filter = ('tags__name',)
    inlines = [TagsRecipesInline]

    def favorite_count(self, obj):
        return obj.favorite_recipes.count()
    favorite_count.admin_order_field = 'favorite_recipes'
    favorite_count.short_description = 'Добавлений в избранное'


@admin.register(TagsRecipes)
class TagsRecipesAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'recipe')
    search_fields = ('tag__name', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'recipe'
    )
    search_fields = ('user__username', 'recipe__name')


@admin.register(FavoriteRecipes)
class FavoriteRecipesAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'recipe',
    )
    list_display_links = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
