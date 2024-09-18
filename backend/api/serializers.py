from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer

from users.models import Subscriber
from recipes.models import Tag, Ingredient, Recipe, IngredientsRecipes

User = get_user_model()


class UserAvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(UserSerializer):
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
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        try:
            Subscriber.objects.get(user=user, subscriber=obj)
        except Subscriber.DoesNotExist:
            return False
        return True


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    name = IngredientsSerializer()
    class Meta:
        model = IngredientsRecipes
        fields = ('id', 'name')


class RecipesSerializer(serializers.ModelSerializer):
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(many=False)
    ingredients = IngredientsInRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_in_shopping_cart(self, obj):
        return 1

    def get_is_favorited(self, obj):
        return 1
