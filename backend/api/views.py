import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from rest_condition import Or
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from common.constants import (AVATAR, ERROR_RECIPE_FAVORITE_DOES_NOT_EXISTS,
                              ERROR_RECIPE_SHOPPING_CART_DOES_NOT_EXISTS,
                              ERROR_SUBSCRIBER_DOES_NOT_EXISTS,
                              ERROR_SUBSCRIBER_IS_ALREADY,
                              ERROR_SUBSCRIBER_USER_USER, ID, SUBSCRIBER,
                              SUBSCRIPTIONS, USER)
from recipes.models import (FavoriteRecipes, Ingredient, Recipe, ShoppingCart,
                            Tag)
from users.models import Subscriber

from .filters import IngredienFilterSet, RecipeFilterSet
from .mixins import ListRetriveMixin
from .pagination import RecipesPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (IngredientsSerializer, RecipesReadSerializer,
                          RecipesWriteSerializer, ShortRecipeSerializer,
                          SubscribeSerializer, TagsSerializer,
                          UserAvatarUpdateSerializer)
from .shopping_cart import get_shopping_list

User = get_user_model()


class UserViewSet(UserViewSet):
    @action(
        ['put'], detail=False, url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def change_avatar(self, request, *args, **kwargs):
        serializer = UserAvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get(AVATAR)
        request.user.avatar = avatar_data
        request.user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}'
        )
        return Response({AVATAR: image_url}, status=status.HTTP_200_OK)

    @change_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    def get_subscriber_user(self, **kwargs):
        return get_object_or_404(User, pk=kwargs[ID])

    @action(
        ['get'], detail=False,
        permission_classes=[IsAuthenticated], url_path=SUBSCRIPTIONS,
        serializer_class=[SubscribeSerializer],
    )
    def subscriptions(self, request, *args, **kwargs):
        all_sub = request.user.users_ubscribers.select_related(
            USER, SUBSCRIBER
        )
        page = self.paginate_queryset(all_sub)
        data = [
            SubscribeSerializer(
                subscriber_obj.subscriber, context={'request': request}).data
            for subscriber_obj in page]
        return self.get_paginated_response(data)

    @action(
        ['post'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated],
        serializer_class=[SubscribeSerializer],
    )
    def subscribe(self, request, *args, **kwargs):
        subscribe_user = self.get_subscriber_user(**kwargs)
        if request.user == subscribe_user:
            return Response(
                ERROR_SUBSCRIBER_USER_USER,
                status=status.HTTP_400_BAD_REQUEST
            )
        obj, result = Subscriber.objects.get_or_create(
            user=request.user, subscriber=subscribe_user)
        if not result:
            return Response(
                ERROR_SUBSCRIBER_IS_ALREADY,
                status=status.HTTP_400_BAD_REQUEST
            )
        data = SubscribeSerializer(
            instance=subscribe_user, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, *args, **kwargs):
        subscribe_user = self.get_subscriber_user(**kwargs)
        subscribe = request.user.users_ubscribers.filter(
            subscriber=subscribe_user
        )
        if not subscribe.exists():
            return Response(
                ERROR_SUBSCRIBER_DOES_NOT_EXISTS,
                status=status.HTTP_400_BAD_REQUEST
            )

        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagsView(ListRetriveMixin):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer


class IngredientsView(ListRetriveMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = IngredienFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.with_related.all()
    filter_backends = [filters.DjangoFilterBackend]
    permission_classes = [Or(IsAuthorOrReadOnly, IsAdminOrReadOnly)]
    filterset_class = RecipeFilterSet
    pagination_class = RecipesPagination

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if not user.is_authenticated:
            return queryset
        shopping_cart_exists = Exists(ShoppingCart.objects.filter(
            user=user, recipe=OuterRef('pk')))
        favorite_recipes_exists = Exists(FavoriteRecipes.objects.filter(
            user=user, recipe=OuterRef('pk')))
        queryset = queryset.annotate(
            is_in_shopping_cart=shopping_cart_exists,
            is_favorited=favorite_recipes_exists
        )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    @action(['get'], detail=True, url_path='get-link',)
    def get_link(self, request, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        short_link = request.build_absolute_uri(f'/s/{recipe.short_link}')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        ['get'], detail=False, url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        file = get_shopping_list(request.user)
        response = FileResponse(open(file, 'rb'))
        os.remove(file)
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
                ERROR_RECIPE_FAVORITE_DOES_NOT_EXISTS,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ShortRecipeSerializer(instance=recipe)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def del_favorite_or_shoping_cart(self, request, model, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        obj = model.objects.filter(user=request.user, recipe=recipe)
        if not obj.exists():
            return Response(
                ERROR_RECIPE_SHOPPING_CART_DOES_NOT_EXISTS,
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
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
        permission_classes=[IsAuthenticated],
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


class ShortLinkRedirectRecipeView(views.APIView):
    def get(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, short_link=kwargs['slug'])
        url = f'{settings.UBSOLUTE_DOMAIN}/recipes/{recipe.id}/'
        return redirect(url)
