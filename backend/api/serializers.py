from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from django.conf import settings

from users.models import Subscriber
from recipes.models import Tag, Ingredient, Recipe, IngredientsRecipes, ShoppingCart, FavoriteRecipes
from utils.short_link_gen import get_link

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
        request = self.context.get('request')
        if not request:
            return False
        if not request.user.is_authenticated:
            return False
        try:
            Subscriber.objects.get(user=request.user, subscriber=obj)
        except Subscriber.DoesNotExist:
            return False
        return True


class SubscribeSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

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
        return len(Recipe.objects.filter(author=obj))

    def get_recipes(self, obj):
        queryset = Recipe.objects.filter(author=obj)
        serializer = ShortRecipeSerializer(instance=queryset, many=True)
        return serializer.data


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


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
        fields = ['id', 'name', 'measurement_unit', 'amount']


class IngredientsInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientsRecipes
        fields = ['id', 'amount']


class RecipesReadSerializer(serializers.ModelSerializer):
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    author = UserSerializer(many=False, read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_in_shopping_cart(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_is_favorited(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return FavoriteRecipes.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_ingredients(self, obj):
        ingredient_in_recipe = IngredientsRecipes.objects.filter(recipe=obj)
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
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы 1 ингридиент.'
            )
        check_unique = []
        for data in value:
            if not Ingredient.objects.filter(pk=data['id']).exists():
                raise serializers.ValidationError(
                    'Какого-то из ингридиентов не существует.'
                )
            if data['id'] in check_unique:
                raise serializers.ValidationError(
                    'Дублирование ингридиента.'
                )
            check_unique.append(data['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы 1 тег.'
            )
        check_unique = []
        for data in value:
            if data in check_unique:
                raise serializers.ValidationError(
                    'Дулбирование тега.'
                )
            check_unique.append(data)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Обязательное поле.'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['short_link'] = get_link()
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for data in ingredients:
            ingredient = Ingredient.objects.get(pk=data['id'])
            IngredientsRecipes.objects.create(
                ingredient=ingredient, recipe=recipe, amount=data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        if (not validated_data.get('tags')
                or not validated_data.get('ingredients')):
            raise serializers.ValidationError(
                {'detail': 'tags или ingredients не заполнены.'}
            )
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        tags = validated_data.get('tags', instance.tags)
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        if ingredients:
            IngredientsRecipes.objects.filter(recipe=instance).delete()
            for data in ingredients:
                ingredient = Ingredient.objects.get(pk=data['id'])
                IngredientsRecipes.objects.create(
                    ingredient=ingredient,
                    recipe=instance,
                    amount=data['amount']
                )
            return instance

    def to_representation(self, instance):
        representation = RecipesReadSerializer(instance)
        return representation.data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['short_link']


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        if obj.image:
            return f'{settings.UBSOLUTE_DOMAIN}/{str(obj.image)}'
        return None
