from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_condition import Or
from rest_framework import filters, status, viewsets, generics
# from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer, UserAvatarUpdateSerializer
from djoser.views import UserViewSet
from django.urls import path
from rest_framework.decorators import action
from django.core.files.base import ContentFile
import base64
from django.conf import settings
import os

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
