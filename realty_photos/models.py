from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from realty import models as realty_models


class RealtyPhoto(models.Model):
    """Realty Photo model."""

    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE,
        verbose_name='Недвижимость',
        related_name='realty_photos',
    )
    image = models.ImageField(upload_to='realty_photos', verbose_name='Фото' )
    sorter = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    class Meta:
        verbose_name = 'Фото недвижимости'
        verbose_name_plural = 'Фото недвижимости'
        ordering = ['sorter']

    def __str__(self):
        return self.image.name


@receiver(post_delete, sender=RealtyPhoto)
def delete_realty_photo_file(sender, instance, **kwargs):

    if instance.image:
        instance.image.delete(save=False)

#     if not instance.id:
#         return

#     try:
#         old_instance = sender.objects.get(
#             id=instance.id)
#     except ObjectDoesNotExist:
#         return

#     if (old_instance and
#             old_instance.file != instance.file):
#         old_instance.file.delete(save=False)
