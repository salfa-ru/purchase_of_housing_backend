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
        realty_models.Realty,
        on_delete=models.CASCADE, verbose_name='Недвижимость', related_name='display_full_info',
    )
    count = models.PositiveIntegerField(verbose_name='Кол-во показов', default=0)

    class Meta:
        verbose_name = 'Показ полной инфо'
        verbose_name_plural = 'Показы полной инфо'

    def __str__(self):
        return f'показов {self.count} --- {self.realty}'

    def increment_view_count(self, request):
        """Increase view count by 1 if the Full Info hasn't been viewed
        in this session or if the last view was more than 5 SECONDS ago."""

        # TODO - Уточнить время таймаута, как часто можно засчитывать новый показ объявления
        # TODO - Сейчас таймаут - 5 секунд

        session_key = f"viewed_realty_{self.realty.id}"
        last_viewed = request.session.get(session_key)

        if last_viewed:
            try:
                last_viewed_time = timezone.datetime.fromisoformat(last_viewed)
                if timezone.now() - last_viewed_time < timedelta(seconds=5):
                    return  # Less than 5 seconds, do not increment
            except (ValueError, TypeError):
                pass  # Если значение last_viewed некорректно, просто игнорируем

        # If no previous view or more than 5 seconds have passed
        self.count = F('count') + 1
        self.save()
        request.session[session_key] = timezone.now().isoformat()  # Update the last viewed time

