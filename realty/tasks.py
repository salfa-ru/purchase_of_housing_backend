import logging
from datetime import timedelta

from django.utils import timezone
from django_q.tasks import Schedule

from config.constants import (
    MAX_LISTING_DURATION,
    STATUS_ACTIVE_ID,
    STATUS_ARCHIVED_ID,
)
from notifications.constants import EXPIRED_CODE
from notifications.utils import create_notification
from realty.models import Realty
from realty_values import models as values_models

logger = logging.getLogger(__name__)


def plan_mass_deactivation():
    """Во время запуска Django создает задачу ежечасной пакетной деактивации устаревших
    объявлений
    """
    now = timezone.now()
    next_hour = now + timedelta(hours=1)
    top_of_next_hour = next_hour.replace(minute=0, second=0, microsecond=0)

    Schedule.objects.filter(func='realty.tasks.expire_all_outdated_realties').delete()

    Schedule.objects.create(
        func='realty.tasks.expire_all_outdated_realties',
        name='Mass Deactivation - HOURLY',
        schedule_type=Schedule.HOURLY,
        next_run=top_of_next_hour,
    )


def expire_realty(realty_id):
    """Деактивирует одно запланированное объявление"""

    logger.info('деактивация объявления %s', realty_id)

    time_threshold = timezone.now() - MAX_LISTING_DURATION

    try:
        realty = Realty.objects.get(
            is_deleted=False,
            id=realty_id,
            realty_status=STATUS_ACTIVE_ID,
            published_at__isnull=False,
            published_at__lte=time_threshold,
        )

        expired_status = values_models.RealtyAdvStatus.objects.get(
            id=STATUS_ARCHIVED_ID
        )
        realty.realty_status = expired_status

        realty.save()

    except Realty.DoesNotExist:
        logger.info(
            'объявление %s не деактивировано: удалено, не активно '
            'или выставлено заново',
            realty_id,
        )
        return

    logger.info('объявление %s деактивировано', realty_id)
    create_notification(realty, EXPIRED_CODE)


def expire_all_outdated_realties():
    """Деактивирует все устаревшие объявления - HOURLY и при запуске DJANGO"""
    expired_status = values_models.RealtyAdvStatus.objects.get(id=STATUS_ARCHIVED_ID)
    time_threshold = timezone.now() - MAX_LISTING_DURATION

    outdated_realties = Realty.objects.filter(
        is_deleted=False,
        realty_status=STATUS_ACTIVE_ID,
        published_at__isnull=False,
        published_at__lte=time_threshold,
    )

    for realty in outdated_realties:
        realty.realty_status = expired_status
        realty.save()

    logger.info('деактивировано объявлений: %s', outdated_realties.count())
