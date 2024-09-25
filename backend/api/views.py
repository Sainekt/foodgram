from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, views, pagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    UserAvatarUpdateSerializer,
    TagsSerializer,
    IngredientsSerializer,
    RecipesReadSerializer,
    RecipesWriteSerializer,
    ShortRecipeSerializer,
    SubscribeSerializer
)
from djoser.views import UserViewSet
from rest_framework.decorators import action
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    ShoppingCart,
    FavoriteRecipes,
)
from users.models import Subscriber
from .filters import IngredientSearchFilter, RecipeFilter, RecipeLimitFiler
from .permissions import IsAuthorOrReadOnly
from django.conf import settings
from django.shortcuts import redirect
from utils.pdf_gen import get_pdf
from django.http import HttpResponse
import os
from .mixins import ListRetriveMixin

User = get_user_model()


class UserViewSet(UserViewSet):

    def delete_avatar_and_file(self, request):
        try:
            os.remove(f'{settings.BASE_DIR}/{settings.MEDIA_URL}'
                      f'{request.user.avatar}')
        except FileNotFoundError:
            pass
        request.user.avatar.delete()

    @action(
        ['put'], detail=False, url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def change_avatar(self, request, *args, **kwargs):
        serializer = UserAvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get('avatar')
        if request.user.avatar:
            self.delete_avatar_and_file(request)
        request.user.avatar = avatar_data
        request.user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}'
        )
        return Response({'avatar': image_url}, status=status.HTTP_200_OK)

    @change_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        self.delete_avatar_and_file(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    def get_subscriber_user(self, **kwargs):
        get_object_or_404(
            User, pk=kwargs['id']
        )

    @action(
        ['get'], detail=False,
        permission_classes=[IsAuthenticated], url_path='subscriptions',
        serializer_class=[SubscribeSerializer],
        filter_backends=[RecipeLimitFiler]
    )
    def subscriptions(self, request, *args, **kwargs):
        all_sub = request.user.users_ubscribers.select_related(
            'user', 'subscriber'
        )
        page = self.paginate_queryset(all_sub)
        data = [
            SubscribeSerializer(subscriber_obj.subscriber).data
            for subscriber_obj in page]
        data = self.filter_queryset(data)
        return self.get_paginated_response(data)

    @action(
        ['post'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated],
        serializer_class=[SubscribeSerializer],
        filter_backends=[RecipeLimitFiler]
    )
    def subscribe(self, request, *args, **kwargs):
        subscribe_user = self.get_subscriber_user(**kwargs)
        if request.user == subscribe_user:
            return Response(
                {'error': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj, result = Subscriber.objects.get_or_create(
            user=request.user, subscriber=subscribe_user)
        if not result:
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = SubscribeSerializer(instance=subscribe_user).data
        filter_data = self.filter_queryset(data)
        return Response(filter_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, *args, **kwargs):
        subscribe_user = self.get_subscriber_user(**kwargs)
        subscribe = request.user.subscribers.filter(subscriber=subscribe_user)
        if not subscribe.exists():
            return Response(
                {'error': 'Подписка на пользователя не найдена.'},
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
    filter_backends = [IngredientSearchFilter]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.with_related.all()
    filter_backends = [RecipeFilter]
    filterset_fields = ['author', 'tags']
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = pagination.PageNumberPagination

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
        data = {}
        shopping_cart = self.request.user.shopping_cart.prefetch_related(
            'user', 'recipe'
        )
        ingredients_in_recipes = [
            i.recipe.recipe_ingredients.all() for i in shopping_cart
        ]
        for ingredients in ingredients_in_recipes:
            for ingredient in ingredients:
                if ingredient.ingredient not in data:
                    data[ingredient.ingredient] = 0
                data[ingredient.ingredient] += ingredient.amount

        pdf_filename = get_pdf(data)
        with open(pdf_filename, 'rb') as file:
            response = HttpResponse(
                file.read(), content_type='application/pdf'
            )
            response[
                'Content-Disposition'] = 'inline; filename="shopping_cart.pdf"'
        os.remove(pdf_filename)
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
        serializer = ShortRecipeSerializer(instance=recipe)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def del_favorite_or_shoping_cart(self, request, model, *args, **kwargs):
        recipe = self.get_recipe(kwargs)
        obj = model.objects.filter(user=request.user, recipe=recipe)
        if not obj.exists():
            return Response(
                {'detail': 'Рецепт в списке покупок не найден.'},
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
