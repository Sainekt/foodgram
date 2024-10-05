from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from common.constants import (AMOUNT, AUTHOR, COOKING_TIME,
                              ERROR_DUBLE_INGREDIENT, ERROR_DUBLE_TAG,
                              ERROR_INGREDIENTS, ERROR_NONE_TAG,
                              ERROR_REQUIRED_FIELD, ERROR_TAGS, ID, IMAGE,
                              INGREDIENTS, IS_FAVORITED, IS_IN_SHOPPING_CART,
                              MEASUREMENT_UNIT, NAME, REQUEST, SHORT_LINK,
                              SLUG, TAGS, TEXT)
from recipes.models import Ingredient, IngredientsRecipes, Recipe, Tag
from users.models import Subscriber
from utils.short_link_gen import get_link

from .mixins import GetUserMixin

User = get_user_model()


class UserAvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(GetUserMixin, UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        if not (user := self.get_user_object()):
            return False
        return Subscriber.objects.filter(user=user, subscriber=obj).exists()


class SubscribeSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_recipes_count(self, obj):
        return len(obj.recipes.all())

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit and limit.isdigit():
            queryset = obj.recipes.all()[:int(limit)]
        else:
            queryset = obj.recipes.all()
        serializer = ShortRecipeSerializer(instance=queryset, many=True)
        return serializer.data


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (ID, NAME, SLUG)


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (ID, NAME, MEASUREMENT_UNIT)


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        read_only=True, source='ingredient.id'
    )
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipes
        fields = [ID, NAME, MEASUREMENT_UNIT, AMOUNT]


class IngredientsInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientsRecipes
        fields = [ID, AMOUNT]


class RecipesReadSerializer(GetUserMixin, serializers.ModelSerializer):
    is_in_shopping_cart = serializers.BooleanField(default=False)
    is_favorited = serializers.BooleanField(default=False)
    author = UserSerializer(many=False, read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            ID, TAGS, AUTHOR, INGREDIENTS, IS_FAVORITED,
            IS_IN_SHOPPING_CART, NAME, IMAGE, TEXT, COOKING_TIME
        )

    def get_ingredients(self, obj):
        ingredient_in_recipe = obj.recipe_ingredients.all()
        data = [
            IngredientsInRecipeSerializer(ingredient).data for ingredient
            in ingredient_in_recipe
        ]
        return data


class RecipesWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = IngredientsInRecipeCreateSerializer(many=True, required=True)

    class Meta:
        model = Recipe
        fields = (
            ID, TAGS, INGREDIENTS,
            NAME, IMAGE, TEXT, COOKING_TIME
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                ERROR_INGREDIENTS
            )
        ingredient_set = {i[ID] for i in value}
        if len(ingredient_set) != len(value):
            raise serializers.ValidationError(ERROR_DUBLE_INGREDIENT)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                ERROR_NONE_TAG
            )
        tags_set = {i for i in value}
        if len(tags_set) != len(value):
            raise serializers.ValidationError(ERROR_DUBLE_TAG)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                ERROR_REQUIRED_FIELD
            )
        return value

    @transaction.atomic
    def create_update_ingredients_tags(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredient_recipe = [IngredientsRecipes(
            ingredient=data[ID],
            recipe=recipe, amount=data[AMOUNT])
            for data in ingredients
        ]
        IngredientsRecipes.objects.bulk_create(ingredient_recipe)

    @transaction.atomic
    def create(self, validated_data):
        validated_data[AUTHOR] = self.context[REQUEST].user
        validated_data[SHORT_LINK] = get_link()
        ingredients = validated_data.pop(INGREDIENTS)
        tags = validated_data.pop(TAGS)
        recipe = Recipe.objects.create(**validated_data)
        self.create_update_ingredients_tags(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if not (tags := validated_data.pop(TAGS, None)):
            raise serializers.ValidationError(
                ERROR_TAGS
            )
        if not (ingredients := validated_data.pop(INGREDIENTS, None)):
            raise serializers.ValidationError(
                ERROR_INGREDIENTS
            )
        super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self.create_update_ingredients_tags(instance, tags, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipesReadSerializer(instance).data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = [SHORT_LINK]


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [ID, NAME, IMAGE, COOKING_TIME]

    def get_image(self, obj):
        if obj.image:
            return f'{settings.UBSOLUTE_DOMAIN}/media/{str(obj.image)}'
        return None
