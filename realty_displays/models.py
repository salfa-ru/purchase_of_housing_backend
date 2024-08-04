from django.db import models

from realty.models import Realty


class DisplayInSearch(models.Model):
    """Display In Search model."""

    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_in_search',
    )
    date = models.DateField(auto_now_add=True, verbose_name='Дата показа')
    count = models.PositiveIntegerField(verbose_name='Кол-во показов')

    class Meta:
        verbose_name = 'Показ в поиске'
        verbose_name_plural = 'Показы в поиске'

    def __str__(self):
        return f'{self.date} показов {self.count} --- {self.realty}'


class DisplayFullInfo(models.Model):
    """Display Full Info model."""

    realty = models.ForeignKey(
        Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_full_info',
    )
    count = models.PositiveIntegerField(verbose_name='Кол-во показов')

    class Meta:
        verbose_name = 'Показ полной инфо'
        verbose_name_plural = 'Показы полной инфо'

    def __str__(self):
        return f'показов {self.count} --- {self.realty}'
