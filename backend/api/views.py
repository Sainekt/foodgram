from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from rest_condition import Or
from rest_framework import filters, status, viewsets, generics, mixins
from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    UserSerializer,
    UserAvatarUpdateSerializer,
    TagsSerializer,
    IngredientsSerializer,
    RecipesReadSerializer,
    RecipesWriteSerializer,
    ShortLinkSerializer,
    ShopingCartSerializer
)
from djoser.views import UserViewSet
from django.urls import path
from rest_framework.decorators import action
from django.core.files.base import ContentFile
import base64
from django.conf import settings
import os
from recipes.models import Tag, Ingredient, Recipe, ShoppingCart, FavoriteRecipes
from .filters import IngredientSearchFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly

User = get_user_model()


class UserViewSet(UserViewSet):

    @action(
        ['put', 'delete'], detail=False, url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def change_avatar(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            self.request.user.avatar = None
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserAvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get('avatar')
        request.user.avatar = avatar_data
        request.user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}'
        )
        return Response({'avatar': str(image_url)}, status=status.HTTP_200_OK)

    @action(["get"], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)


class TagsView(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsView(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = [IngredientSearchFilter]
    search_fields = ['^name',]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [RecipeFilter]
    filterset_fields = ['author', 'tags']
    permission_classes = [IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    @action(['get'], detail=True, url_path='get-link',)
    def get_link(self, request, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        short_link = (
            f'{request.scheme}://' + request.META['HTTP_HOST']
            + f'/s/{recipe.short_link}'
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        ['get'], detail=False, url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        # Создаем текст файла
        text = "Это текст файла.\n"
        # Создаем ответ
        response = Response(text, content_type='text/plain')
        # Установка заголовка Content-Disposition для загрузки файла
        response.headers["Content-Disposition"] = "attachment; filename=my_file.txt"
        return response

    def get_recipe(self, kwargs):
        return get_object_or_404(Recipe, pk=kwargs['pk'])

    def add_favorite_or_shoping_cart(self, request, model, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        shoping_add, created = model.objects.get_or_create(
            recipe=recipe, user=request.user
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ShopingCartSerializer(instance=recipe)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def del_favorite_or_shoping_cart(self, request, model, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        shoping_cart = get_object_or_404(
            model, user=request.user, recipe=recipe
        )
        shoping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['post'], detail=True, url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def add_shoping_cart(self, request, *args, **kwargs):
        return self.add_favorite_or_shoping_cart(
            request, ShoppingCart, *args, **kwargs
        )

    @add_shoping_cart.mapping.delete
    def del_shoping_cart(self, request, *args, **kwargs):
        return self.del_favorite_or_shoping_cart(
            request, ShoppingCart, *args, **kwargs
        )

    @action(
        ['post'], detail=True, url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def add_favorite(self, request, *args, **kwargs):
        return self.add_favorite_or_shoping_cart(
            request, FavoriteRecipes, *args, **kwargs
        )

    @add_favorite.mapping.delete
    def del_favorite(self, request, *args, **kwargs):
        return self.del_favorite_or_shoping_cart(
            request, FavoriteRecipes, *args, **kwargs
        )
