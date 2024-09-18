from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404
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
)
from djoser.views import UserViewSet
from django.urls import path
from rest_framework.decorators import action
from django.core.files.base import ContentFile
import base64
from django.conf import settings
import os
from recipes.models import Tag, Ingredient, Recipe
from .filters import CustomSearchFilter

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
    filter_backends = [CustomSearchFilter]
    search_fields = ['^name',]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author', 'tags']

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer
