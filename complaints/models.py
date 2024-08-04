from django.db import models

from realty.models import Realty
from users.models import User
from config.constants import COMPLAINT_LENGTH


class Complaint(models.Model):
    """Complaint model."""

    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT, verbose_name='Владелец', related_name='complaints',
    )
    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='complaints',
    )
    description = models.TextField(
        max_length=COMPLAINT_LENGTH, verbose_name='Описание',
    )
    is_new = models.BooleanField(
        default=True, verbose_name='Новое'
    )

    class Meta:
        ordering = ("-is_new",)
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'

    def __str__(self):
        return (f'{self.description[:20]}'
                f'{"..." if len(self.description) > 20 else ""} ')
