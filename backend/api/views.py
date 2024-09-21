from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from rest_condition import Or
from rest_framework import filters, status, viewsets, generics, mixins
from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    UserAvatarUpdateSerializer,
    TagsSerializer,
    IngredientsSerializer,
    RecipesReadSerializer,
    RecipesWriteSerializer,
    ShortRecipeSerializer,
    ShortLinkSerializer,
    UserSerializer,
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

User = get_user_model()


class UserViewSet(UserViewSet):

    @action(
        ['put'], detail=False, url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def change_avatar(self, request, *args, **kwargs):
        serializer = UserAvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get('avatar')
        request.user.avatar = avatar_data
        request.user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}'
        )
        return Response({'avatar': str(image_url)}, status=status.HTTP_200_OK)

    @change_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        self.request.user.avatar = None
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(
        ['get'], detail=False,
        permission_classes=[IsAuthenticated], url_path='subscriptions',
        serializer_class=[SubscribeSerializer],
        filter_backends=[RecipeLimitFiler]
    )
    def subscriptions(self, request, *args, **kwargs):
        all_sub = request.user.users_ubscribers.all()
        filter_sub = self.filter_queryset(all_sub)
        page = self.paginate_queryset(filter_sub)
        data = [
            SubscribeSerializer(subscriber.subscriber).data
            for subscriber in page]
        return self.get_paginated_response(data)

    @action(
        ['post'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated],
        serializer_class=[SubscribeSerializer],
        filter_backends=[RecipeLimitFiler]
    )
    def subscribe(self, request, *args, **kwargs):
        subscribe_on = get_object_or_404(
            User, pk=kwargs['id']
        )
        if request.user == subscribe_on:
            return Response(
                {'error': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj, result = Subscriber.objects.get_or_create(
            user=request.user, subscriber=subscribe_on)
        if not result:
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = SubscribeSerializer(instance=subscribe_on).data
        filter_data = self.filter_queryset(data)
        return Response(filter_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, *args, **kwargs):
        subscribe_user = get_object_or_404(User, pk=kwargs['id'])
        subscribe = Subscriber.objects.filter(
            user=request.user, subscriber=subscribe_user
        )
        if not subscribe.exists():
            return Response(
                {'error': 'Подписка на пользователя не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
