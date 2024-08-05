from django.db import models

from realty.models import Realty
from users.models import User


class Chat(models.Model):
    """Chat model."""

    user_from = models.ForeignKey(
        User,
        on_delete=models.PROTECT, verbose_name='От кого', related_name='chats_from_me',
    )
    user_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT, verbose_name='Кому', related_name='chats_to_me',
    )
    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='chats',
    )
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='Дата+Время')
    message = models.TextField(verbose_name='Сообщение',)
    is_new = models.BooleanField(default=True, verbose_name='Новое')
    is_deleted_from = models.BooleanField(default=False, verbose_name='Удалено (от кого)')
    is_deleted_to = models.BooleanField(default=False, verbose_name='Удалено (кому)')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return (f'{self.message[:20]}'
                f'{"..." if len(self.message) > 20 else ""} ')
