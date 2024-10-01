from django.db import models

from config.constants import SHORT_STR_LENGTH
from realty import models as realty_models
from users import models as users_models


class Chat(models.Model):
    """Chat model."""

    user_from = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='От кого',
        related_name='chats_from_me',
    )
    user_to = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Кому',
        related_name='chats_to_me',
    )
    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE,
        verbose_name='Недвижимость',
        related_name='chats',
    )
    datetime = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата+Время'
    )
    message = models.TextField(verbose_name='Сообщение',)
    is_new = models.BooleanField(default=True, verbose_name='Новое')
    is_deleted_from = models.BooleanField(
        default=False, verbose_name='Удалил (от кого)'
    )
    is_deleted_to = models.BooleanField(
        default=False, verbose_name='Удалил (кому)'
    )
    is_blocked_from = models.BooleanField(
        default=False, verbose_name='Заблокировал (от кого)'
    )
    is_blocked_to = models.BooleanField(
        default=False, verbose_name='Заблокировал (кому)'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return (f'{self.message[:SHORT_STR_LENGTH]}'
                f'{"..." if len(self.message) > SHORT_STR_LENGTH else ""} ')
