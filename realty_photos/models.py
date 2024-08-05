from django.db import models

from realty.models import Realty


class RealtyPhoto(models.Model):
    """Realty Photo model."""

    realty = models.ForeignKey(
        Realty,
        on_delete=models.PROTECT, verbose_name='Недвижимость', related_name='realty_photos',
    )
    image = models.ImageField(upload_to='realty_photos', verbose_name='Фото')

    class Meta:
        verbose_name = 'Фото недвижимости'
        verbose_name_plural = 'Фото недвижимости'

    def __str__(self):
        return self.image.name
