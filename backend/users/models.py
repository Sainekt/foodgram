from django.contrib.auth.models import AbstractUser
from django.db import models


from common.constants import MAX_254, MAX_150


class User(AbstractUser):

    email = models.EmailField(
        verbose_name='Адрес электронной почты.',
        unique=True,
        error_messages={
            'unique': 'Адрес электронной почты уже используется.'
        },
        max_length=MAX_254
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_150,
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.'
        }
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_150,
    )
    avatar = models.ImageField(
        verbose_name='Фото',
        upload_to='users/avatar/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscriber(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='users_ubscribers'
    )
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriber'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscriber'], name='unique_user_subscriber'
            )
        ]
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
