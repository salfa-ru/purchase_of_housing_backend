from django.utils import timezone
from datetime import timedelta

from django.db import models
from django.db.models import F

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

    def increment_search_count(self, request):
        """Увеличение счетчика показа в поиске с защитой от накрутки."""

        # TODO - Уточнить время таймаута DisplayInSearch
        timeout = timedelta(hours=0, minutes=0, seconds=5)

        key = "realty_search_view"

        is_unique = is_unique_view(request, self.realty.id, timeout, key)

        if is_unique:
            self.count = F('count') + 1
            self.save()

        return


class DisplayFullInfo(models.Model):
    """Display Full Info model."""

    realty = models.ForeignKey(
        realty_models.Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_full_info',
    )
    # теперь даты появляются в показах полных объявлений
    date = models.DateField(auto_now_add=True, verbose_name='Дата показа')
    count = models.PositiveIntegerField(verbose_name='Кол-во показов', default=0)

    class Meta:
        verbose_name = 'Показ полной инфо'
        verbose_name_plural = 'Показы полной инфо'

    def __str__(self):
        return f'{self.date} показов {self.count} --- {self.realty}'

    def increment_view_count(self, request):
        """Увеличение счетчика полных просмотров с защитой от накрутки."""

        # TODO - Уточнить время таймаута FullInfo
        timeout = timedelta(hours=0, minutes=0, seconds=20)

        key = "realty_full_view"

        is_unique = is_unique_view(request, self.realty.id, timeout, key)

        if is_unique:
            self.count = F('count') + 1
            self.save()

        return


def is_unique_view(request, realty_id, timeout, key):
    session_key = f"{key}_{realty_id}"
    last_viewed = request.session.get(session_key)

    if last_viewed:
        try:
            last_viewed_time = timezone.datetime.fromisoformat(last_viewed)
            if timezone.now() - last_viewed_time < timeout:
                return False  # счетчик не трогаем, объявление показывалось недавно
        except (ValueError, TypeError):
            pass  # Если значение last_viewed некорректно, просто игнорируем

    # Обновить время последнего просмотра
    # Просмотр обновляется ДО внесения изменения в базу!
    request.session[session_key] = timezone.now().isoformat()
    return True
