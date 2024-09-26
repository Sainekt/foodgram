from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from django.conf import settings

from recipes.models import (
    Tag, Ingredient, Recipe, IngredientsRecipes
)
from utils.short_link_gen import get_link
from common.constants import (
    ID, TAGS, AUTHOR, INGREDIENTS, SLUG,
    IS_FAVORITED, IS_IN_SHOPPING_CART, NAME, IMAGE, TEXT,
    COOKING_TIME, SHORT_LINK, ERROR_INGREDIENTS, ERROR_TAGS,
    ERROR_REQUIRED_FIELD, ERROR_DUBLE_TAG, ERROR_NONE_TAG,
    ERROR_DUBLE_INGREDIENT, ERROR_DOES_NOT_EXISTS_INGRIDIENT, REQUEST,
    INGREDIENT, AMOUNT, MEASUREMENT_UNIT
)

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
        return user.subscribers.all().exists()


class SubscribeSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

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
        queryset = obj.recipes.all()
        serializer = ShortRecipeSerializer(instance=queryset, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        # Сериализирует данные только подписчиков, всегда True
        return True


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
        read_only=True, source=f'{INGREDIENT}.{ID}'
    )
    name = serializers.CharField(read_only=True, source=f'{INGREDIENT}.{NAME}')
    measurement_unit = serializers.CharField(
        read_only=True, source=f'{INGREDIENT}.{MEASUREMENT_UNIT}'
    )

    class Meta:
        model = IngredientsRecipes
        fields = [ID, NAME, MEASUREMENT_UNIT, AMOUNT]


class IngredientsInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientsRecipes
        fields = [ID, AMOUNT]


class RecipesReadSerializer(GetUserMixin, serializers.ModelSerializer):
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    author = UserSerializer(many=False, read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            ID, TAGS, AUTHOR, INGREDIENTS, IS_FAVORITED,
            IS_IN_SHOPPING_CART, NAME, IMAGE, TEXT, COOKING_TIME
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.get_user_object()
        return obj.shopping_cart.filter(user=user).exists()

    def get_is_favorited(self, obj):
        user = self.get_user_object()
        return obj.favorite_recipes.filter(user=user).exists()

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
        check_unique = set()
        queryset = Ingredient.objects.all()
        validate_ingredients = []
        for data in value:
            if not (ingredient := queryset.filter(pk=data[ID])):
                raise serializers.ValidationError(
                    ERROR_DOES_NOT_EXISTS_INGRIDIENT
                )
            if data[ID] in check_unique:
                raise serializers.ValidationError(
                    ERROR_DUBLE_INGREDIENT
                )
            check_unique.add(data[ID])
            validate_ingredients.append(
                {
                    # queryset всегда с 1 элементом.
                    INGREDIENT: ingredient[0],
                    AMOUNT: data[AMOUNT]
                }
            )

        return validate_ingredients

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                ERROR_NONE_TAG
            )
        check_unique = set()
        for data in value:
            if data in check_unique:
                raise serializers.ValidationError(
                    ERROR_DUBLE_TAG
                )
            check_unique.add(data)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                ERROR_REQUIRED_FIELD
            )
        return value

    def create_update_ingredients_tags(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        ingredient_recipe = [IngredientsRecipes(
            ingredient=data[INGREDIENT],
            recipe=recipe, amount=data[AMOUNT])
            for data in ingredients
        ]
        IngredientsRecipes.objects.bulk_create(ingredient_recipe)

    def create(self, validated_data):
        validated_data[AUTHOR] = self.context[REQUEST].user
        validated_data[SHORT_LINK] = get_link()
        ingredients = validated_data.pop(INGREDIENTS)
        tags = validated_data.pop(TAGS)
        recipe = Recipe.objects.create(**validated_data)
        self.create_update_ingredients_tags(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        if not (tags := validated_data.pop(TAGS, None)):
            raise serializers.ValidationError(
                ERROR_TAGS
            )
        if not (ingredients := validated_data.pop(INGREDIENTS, None)):
            raise serializers.ValidationError(
                ERROR_INGREDIENTS
            )
        instance.image = validated_data.get(IMAGE, instance.image)
        instance.name = validated_data.get(NAME)
        instance.text = validated_data.get(TEXT)
        instance.cooking_time = validated_data.get(COOKING_TIME)
        instance.save()
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
            return f'{settings.UBSOLUTE_DOMAIN}/{str(obj.image)}'
        return None
