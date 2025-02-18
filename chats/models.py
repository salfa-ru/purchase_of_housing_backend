from django.db import models
from django.db.models import UniqueConstraint

from realty import models as realty_models
from users import models as users_models

from config.constants import SHORT_STR_LENGTH


class Chat(models.Model):
    """
    Модель чата между владельцем недвижимости и потенциальным клиентом.
    Чат может быть создан только клиентом.
    """
    chat_id = models.AutoField(primary_key=True)
    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE,
        verbose_name='Объект недвижимости',
        related_name='chats'
    )
    owner = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Владелец недвижимости',
        related_name='owner_chats'
    )
    client = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Клиент',
        related_name='client_chats'
    )

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        constraints = [
            UniqueConstraint(
                fields=['realty', 'owner', 'client'],
                name='unique_chat_participants'
            )
        ]

    def __str__(self):
        return f'Чат {self.chat_id}: {self.client} → {self.owner} -- {self.realty}'


class Message(models.Model):
    """ Message - переименованная модель, ранее была названа Chat """

    msg_id = models.AutoField(primary_key=True, verbose_name='Message ID')
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат',
        # default=0, # только для первой миграции
    )
    user_from = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Отправитель',
        related_name='messages_sent'
    )
    user_to = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Получатель',
        related_name='messages_received'
    )
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(verbose_name='Дата + Время создания', auto_now_add=True)
    read_at = models.DateTimeField(verbose_name='Дата + Время прочтения', null=True, blank=True)

    is_new = models.BooleanField(default=True, verbose_name='Не прочитано')

    is_deleted_from = models.BooleanField(default=False, verbose_name='Удалено отправителем')
    is_deleted_to = models.BooleanField(default=False, verbose_name='Удалено получателем')

    sender_is_owner = models.BooleanField(verbose_name='отправлено владельцем')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return (f'{self.message[:SHORT_STR_LENGTH]}'
                f'{"..." if len(self.message) > SHORT_STR_LENGTH else ""} ')

    """ Что то совсем новенькое """
    def save(self, *args, **kwargs):
        # Автоматически устанавливаем sender_is_owner при сохранении
        if not self.pk:  # Только для новых сообщений
            self.sender_is_owner = (self.user_from == self.chat.owner)
        super().save(*args, **kwargs)


class Blocking(models.Model):
    user_who = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Кто заблокировал',
        related_name='who_blocked',
    )
    user_whom = models.ForeignKey(
        users_models.User,
        on_delete=models.PROTECT,
        verbose_name='Кого заблокировали',
        related_name='whom_blocked',
    )

    class Meta:
        verbose_name = 'Блокировка'
        verbose_name_plural = 'Блокировки'

    def __str__(self):
        return f'{self.user_who} - {self.user_whom}'
