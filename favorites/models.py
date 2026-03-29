from django.db import models
from users import models as user_models
from realty.models import Realty


class Favorite(models.Model):
    """Избранное пользователя."""

    user = models.ForeignKey(
        user_models.User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Объявление',
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )
    is_viewed = models.BooleanField(
        default=False,
        verbose_name='Просмотрено',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'realty')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', 'is_viewed']),
            models.Index(fields=['realty']),
        ]

    def __str__(self):
        return f'{self.user} -> {self.realty.id}'
