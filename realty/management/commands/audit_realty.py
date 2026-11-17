"""Ревизия объявлений: ищет записи, которые не могли появиться через API.

Без флагов только печатает отчёт. С флагом --fix чинит то, что чинится
однозначно: снимает коммерческий тип у жилых объявлений и помечает удалёнными
объявления без сделки. Остальное показывается в отчёте и правится руками."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from config.constants import PUBLISHER_PARTICIPANTS
from realty.models import Realty

MOSCOW_LATITUDE = (54.2, 56.9)
MOSCOW_LONGITUDE = (35.1, 39.1)


def describe(realty):
    return f'#{realty.id} «{realty.realty_type.type}», владелец {realty.owner_id}'


class Command(BaseCommand):
    help = 'Ищет противоречивые объявления. С --fix исправляет однозначные случаи.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Исправить то, что чинится однозначно',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        base = Realty.objects.select_related(
            'realty_type', 'address', 'owner_type'
        ).filter(is_deleted=False)

        without_trade = base.filter(
            sale_profile__isnull=True, rent_profile__isnull=True
        )
        commercial_type_on_residential = (
            base.filter(realty_type__is_commercial=False)
            .exclude(commercial_type__isnull=True)
            .exclude(commercial_type='')
        )
        characteristics_on_residential = base.filter(
            realty_type__is_commercial=False, commercial_characteristics__isnull=False
        )
        commercial_without_characteristics = base.filter(
            realty_type__is_commercial=True, commercial_characteristics__isnull=True
        )
        strange_coordinates = base.exclude(
            address__latitude__range=MOSCOW_LATITUDE,
            address__longitude__range=MOSCOW_LONGITUDE,
        )
        strange_owner_type = base.exclude(
            Q(owner_type__participant__in=PUBLISHER_PARTICIPANTS)
        )
        blank_payment_participant = base.filter(
            Q(rent_profile__lease_payments__counters_payment__participant='')
            | Q(rent_profile__lease_payments__communal_payment__participant='')
        )

        self.report('Без продажи и без аренды', without_trade)
        self.report(
            'Коммерческий тип у жилого объявления', commercial_type_on_residential
        )
        self.report(
            'Характеристики помещения у жилого объявления',
            characteristics_on_residential,
        )
        self.report(
            'Коммерческое объявление без характеристик помещения',
            commercial_without_characteristics,
        )
        self.report('Координаты вне Москвы', strange_coordinates)
        self.report('Публикатор не «Собственник» и не «Агент»', strange_owner_type)
        self.report('Платежи аренды с пустым участником', blank_payment_participant)

        if not fix:
            self.stdout.write(
                self.style.HTTP_INFO(
                    '\nЭто только отчёт. Запустите с --fix, чтобы снять лишний '
                    'коммерческий тип и пометить удалёнными объявления без сделки.'
                )
            )
            return

        with transaction.atomic():
            cleared = commercial_type_on_residential.update(commercial_type=None)
            hidden = without_trade.update(is_deleted=True)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nСнят коммерческий тип: {cleared}. '
                f'Помечено удалёнными объявлений без сделки: {hidden}.'
            )
        )
        self.stdout.write(
            self.style.HTTP_INFO(
                'Остальное из отчёта правится руками: данные могут быть настоящими.'
            )
        )

    def report(self, title, queryset):
        """Печатает заголовок, количество и первые объявления списка."""
        found = list(queryset[:20])
        total = queryset.count()
        if not total:
            self.stdout.write(self.style.SUCCESS(f'{title}: нет'))
            return

        self.stdout.write(self.style.WARNING(f'{title}: {total}'))
        for realty in found:
            self.stdout.write(f'  {describe(realty)}')
        if total > len(found):
            self.stdout.write(f'  … и ещё {total - len(found)}')
