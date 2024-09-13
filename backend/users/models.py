from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


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
