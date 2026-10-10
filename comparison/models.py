from django.db import models

from config.constants import STATUS_ACTIVE_ID
from realty.models import Realty
from users import models as user_models


class Comparison(models.Model):
    """Объявление в списке сравнения пользователя."""

    user = models.ForeignKey(
        user_models.User,
        on_delete=models.CASCADE,
        related_name='comparisons',
        verbose_name='Пользователь',
    )
    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE,
        related_name='compared_by',
        verbose_name='Объявление',
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Сравнение'
        verbose_name_plural = 'Сравнение'
        unique_together = ('user', 'realty')
        ordering = ['added_at', 'id']

    def __str__(self):
        return f'{self.user} -> {self.realty_id}'

    @property
    def is_realty_deleted(self):
        """Объявление удалено само или вместе с аккаунтом владельца."""
        return self.realty.is_deleted or self.realty.owner.is_deleted

    @property
    def is_available(self):
        """Объявление можно смотреть: опубликовано, не удалено, владелец на месте.
        Удалённые и архивные остаются в списке, но помечаются недоступными."""
        return (
            not self.is_realty_deleted
            and self.realty.realty_status_id == STATUS_ACTIVE_ID
        )
