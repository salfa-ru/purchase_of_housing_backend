from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from realty import models as realty_models


class DisplayInSearch(models.Model):
    """Display In Search model."""

    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_in_search',
    )
    count = models.PositiveIntegerField(verbose_name='Кол-во показов', default=0)

    class Meta:
        verbose_name = 'Показ в поиске'
        verbose_name_plural = 'Показы в поиске'

    def __str__(self):
        return f'показов {self.count} --- {self.realty}'


class DisplayFullInfo(models.Model):
    """Display Full Info model."""

    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_full_info',
    )
    # теперь даты появляются в показах полных объявлений
    date = models.DateField(default=timezone.now, verbose_name='Дата показа')
    count = models.PositiveIntegerField(verbose_name='Кол-во показов', default=0)

    class Meta:
        verbose_name = 'Показ полной инфо'
        verbose_name_plural = 'Показы полной инфо'

    def __str__(self):
        return f'{self.date} показов {self.count} --- {self.realty}'


@receiver(post_save, sender=realty_models.Realty)
def delete_counters_if_status_not_active(sender, instance, **kwargs):
    """ Удаляет все счетчики объявления при выключении активного статуса """

    # Проверяем, что статус недвижимости не равен 1 - объявление не активно
    if instance.realty_status_id != 1:
        # Удаляем связанные записи из DisplayInSearch
        DisplayInSearch.objects.filter(realty=instance).delete()

        # Удаляем связанные записи из DisplayFullInfo
        DisplayFullInfo.objects.filter(realty=instance).delete()
