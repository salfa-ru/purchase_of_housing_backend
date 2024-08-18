import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser

from config import constants
from realty_values import models as values_models


class User(AbstractUser):
    """Custom User model."""
    uuid_esa = models.UUIDField(
        editable=False,
        verbose_name='UUID из ЕСА',
        **constants.NULLABLE_FIELD
    )

    avatar = models.ImageField(
        upload_to='users/avatars',
        verbose_name='Аватарка',
        **constants.NULLABLE_FIELD,
    )
    user_type = models.ForeignKey(
        values_models.TradeParticipant,
        on_delete=models.PROTECT,
        verbose_name='Тип пользователя',
        related_name='users',
        **constants.NULLABLE_FIELD,
    )
    phone_number = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name='Номер телефона',
        **constants.NULLABLE_FIELD,
    )
    updated_at = models.DateTimeField(
        verbose_name='Последнее изменение',
        default=None,
        **constants.NULLABLE_FIELD,
    )
    # TODO доделать генерацию qr-кода
    # phone_qr_code = models.ImageField(
    #     upload_to='users/phone_qr_codes',
    #     verbose_name='QR-код телефона',
    #     ** constants.NULLABLE_FIELD,
    # )

