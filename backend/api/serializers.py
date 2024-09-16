from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer

from users.models import Subscriber

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
