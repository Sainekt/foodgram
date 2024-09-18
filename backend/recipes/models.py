from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from common.constants import MAX_32, MAX_128, MAX_64, MAX_256

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=MAX_32, verbose_name='Название')
    slug = models.SlugField(max_length=MAX_32, verbose_name='Слаг')


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_128
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_64
    )


class IngredientsRecipes(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.IntegerField(
        verbose_name='Количество игридиента',
        validators=[MinValueValidator(1)],
    )


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        through=IngredientsRecipes,
        related_name='ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagsRecipes',
        related_name='recipes'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_256,
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[MinValueValidator(1)]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    short_link = models.CharField(
        verbose_name='Короткая ссылка',
        max_length=10,
    )


class TagsRecipes(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, related_name='recipe_tags'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_tags'
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )


class FavoriteRecipes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
