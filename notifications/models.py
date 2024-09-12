from django.db import models

from config.constants import NOTIFICATION_LENGTH, NULLABLE_FIELD
from realty import models as realty_models
from users import models as users_models


class NotificationTemplate(models.Model):
    """Notification Template model."""
    code = models.CharField(
        max_length=NOTIFICATION_LENGTH['code'], verbose_name='Код',
    )
    part1 = models.CharField(
        max_length=NOTIFICATION_LENGTH['part1'], verbose_name='Первая часть',
    )
    part2 = models.CharField(
        max_length=NOTIFICATION_LENGTH['part2'], verbose_name='Вторая часть',
        **NULLABLE_FIELD
    )

    class Meta:
        verbose_name = 'Шаблон уведомления'
        verbose_name_plural = 'Шаблоны уведомлений'

    def __str__(self):
        return self.code


class Notification(models.Model):
    """Notification model."""

    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.PROTECT,
        verbose_name='Шаблон',
        related_name='notifications',
    )
    user_to = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Кому',
        related_name='notifications',
    )
    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.PROTECT,
        verbose_name='Недвижимость',
        related_name='notifications',
    )
    datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата+Время'
    )
    is_new = models.BooleanField(default=True, verbose_name='Новое')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-datetime', ]

    def __str__(self):
        return f'{self.template} --- {self.realty}'
