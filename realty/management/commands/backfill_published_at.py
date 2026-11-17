"""Разовая команда: проставляет дату публикации активным объявлениям,
у которых её нет."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from config.constants import STATUS_ACTIVE_ID
from realty.models import Realty


class Command(BaseCommand):
    help = 'Проставляет дату публикации активным объявлениям, у которых её нет.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Записать дату, а не только посчитать',
        )

    def handle(self, *args, **options):
        without_date = Realty.objects.filter(
            is_deleted=False,
            realty_status=STATUS_ACTIVE_ID,
            published_at__isnull=True,
        )
        total = without_date.count()

        if not total:
            self.stdout.write(
                self.style.SUCCESS('Активных объявлений без даты публикации нет.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Активных объявлений без даты публикации: {total}')
        )

        if not options['fix']:
            self.stdout.write(
                self.style.HTTP_INFO(
                    'Это только подсчёт. Запустите с --fix, чтобы проставить дату. '
                    'Объявления получат текущее время, и отсчёт срока публикации '
                    'начнётся для них заново.'
                )
            )
            return

        updated = without_date.update(published_at=timezone.now())
        self.stdout.write(
            self.style.SUCCESS(f'Дата публикации проставлена: {updated}.')
        )
