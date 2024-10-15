from io import BytesIO

import qrcode
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.signals import pre_save
from django.dispatch import receiver

from config import constants
from config.constants import IMAGE_EXTENSIONS, MAX_AVATAR_SIZE
from realty_values import models as values_models


def validate_avatar_size(value):
    filesize = value.size
    if filesize > MAX_AVATAR_SIZE:
        raise ValidationError('The allowed file size has been exceeded')


class CustomUserManager(UserManager):
    """Переопределение работы менеджера, для того чтобы работала команда createsuperuser.
    Для superuser задаются значения для обязательных полей."""

    def create_superuser(self, username, email=None, password=None,
                         **extra_fields):
        email = username + '@email.com'
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("first_name", username)
        extra_fields.setdefault("last_name", username)
        extra_fields.setdefault("phone_number", username + '_phone')
        return super().create_superuser(username, email, password,
                                        **extra_fields)


class User(AbstractUser):
    """Custom User model."""
    objects = CustomUserManager()
    REQUIRED_FIELDS = []

    first_name = models.CharField(verbose_name='Имя',
                                  max_length=constants.CHAR_LENGTH)
    last_name = models.CharField(verbose_name='Фамилия',
                                 max_length=constants.CHAR_LENGTH)
    email = models.EmailField(verbose_name='email', unique=True)

    uuid_esa = models.UUIDField(
        editable=False,
        verbose_name='UUID из ЕСА',
        **constants.NULLABLE_FIELD
    )

    avatar = models.ImageField(
        upload_to='users/avatars',
        verbose_name='Аватарка',
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size
        ],
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
        unique=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='Последнее изменение',
        default=None,
        **constants.NULLABLE_FIELD,
    )

    phone_qr_code = models.ImageField(
        upload_to='users/phone_qr_codes',
        verbose_name='QR-код телефона',
        **constants.NULLABLE_FIELD,
    )

    def save(self, *args, **kwargs):
        """Хэшируем пароль.
         Меняем username для 'своих' пользователей (при замене email).
         Создаем QR-code, если изменился телефон.
         Удаляем старую аватарку (файл), если аватарка меняется."""
        password_previous = None
        email_previous = None
        phone_number_previous = None
        uuid_esa = None
        user_previous = None
        avatar_previous = None

        if self.pk:
            user_previous = User.objects.get(pk=self.pk)
            password_previous = user_previous.password
            email_previous = user_previous.email
            phone_number_previous = user_previous.phone_number
            uuid_esa = user_previous.uuid_esa
            avatar_previous = user_previous.avatar

        # Хэшируем пароль
        if not self.is_superuser and (
                self._state.adding or self.password != password_previous):
            self.set_password(self.password)

        # Меняем username для 'своих' пользователей
        if not uuid_esa and (
                self._state.adding or self.email != email_previous):
            self.username = self.email

        # Создаем QR-код при создании пользователя или обновлении номера телефона,
        # старый при необходимости удаляем
        if self._state.adding or self.phone_number != phone_number_previous:
            img = create_qrcode(self.phone_number)
            file_name = f'{self.phone_number}.png'
            self.phone_qr_code.save(
                file_name,
                ContentFile(img.read()),
                save=False,
            )
            if user_previous:
                user_previous.phone_qr_code.delete()

        # Удаляем старую аватарку при замене
        if user_previous and self.avatar != avatar_previous:
            user_previous.avatar.delete(save=False)

        return super().save(*args, **kwargs)


@receiver(pre_save, sender=User)
def set_default_user_type(sender, instance, *args, **kwargs):
    """Устанавливает дефолтное значение user_type. Используется для MVP"""
    if not instance.pk:
        user_type, _ = values_models.TradeParticipant.objects.get_or_create(
            participant=constants.USER_TYPE_DEFAULT
        )
        instance.user_type = user_type


def create_qrcode(phone_number):
    """Создает QR-код по номеру телефона,
    возвращает изображение"""

    img = qrcode.make('tel:' + phone_number)
    img_bytes = BytesIO()
    img.save(img_bytes, format='png')
    img_bytes.seek(0)

    return img_bytes
