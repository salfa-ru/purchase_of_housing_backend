from django.db import models

from config.constants import DEVICE_TOKEN_LENGTH, NOTIFICATION_LENGTH, NULLABLE_FIELD
from realty import models as realty_models
from users import models as users_models


class NotificationTemplate(models.Model):
    """Шаблон уведомления."""

    code = models.CharField(
        max_length=NOTIFICATION_LENGTH['code'],
        verbose_name='Код',
    )
    part1 = models.CharField(
        max_length=NOTIFICATION_LENGTH['part1'],
        verbose_name='Первая часть',
    )
    part2 = models.CharField(
        max_length=NOTIFICATION_LENGTH['part2'],
        verbose_name='Вторая часть',
        **NULLABLE_FIELD,
    )

    class Meta:
        verbose_name = 'Шаблон уведомления'
        verbose_name_plural = 'Шаблоны уведомлений'

    def __str__(self):
        return self.code


class Notification(models.Model):
    """Уведомление."""

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата+Время')
    is_new = models.BooleanField(default=True, verbose_name='Новое')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = [
            '-created_at',
        ]

    def __str__(self):
        return f'{self.template} --- {self.realty}'


class DeviceToken(models.Model):
    """Токен устройства пользователя для пуш-уведомлений (FCM)."""

    ANDROID = 'android'
    IOS = 'ios'
    WEB = 'web'
    PLATFORM_CHOICES = [
        (ANDROID, 'Android'),
        (IOS, 'iOS'),
        (WEB, 'Web'),
    ]

    user = models.ForeignKey(
        users_models.User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='device_tokens',
    )
    token = models.CharField(
        max_length=DEVICE_TOKEN_LENGTH,
        unique=True,
        verbose_name='Токен устройства',
    )
    platform = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES,
        verbose_name='Платформа',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')

    class Meta:
        verbose_name = 'Токен устройства'
        verbose_name_plural = 'Токены устройств'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} --- {self.platform}'
