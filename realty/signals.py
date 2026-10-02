import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import Schedule

from config.constants import (
    MAX_LISTING_DURATION,
    STATUS_ACTIVE_ID,
    STATUS_ARCHIVED_ID,
    STATUS_ON_MODERATION_ID,
    STATUS_REJECTED_ID,
)
from notifications.constants import (
    ARCHIVED_CODE,
    BLOCKED_CODE,
    DELETED_CODE,
    ON_MODERATION_CODE,
    PUBLISHED_CODE,
    REJECTED_CODE,
)
from notifications.utils import create_notification
from realty.models import Realty

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Realty)
def handle_realty_save(sender, instance, **kwargs):
    """Обработка сохранения объявления:
    - установка статуса "на модерации" новому объявлению
    - создание уведомлений при смене статусов
    - создание задач для django q2 на деактивацию объявлений"""

    if hasattr(instance, '_pre_save_in_progress'):
        return

    instance._pre_save_in_progress = True

    is_new = instance.id is None

    if is_new:
        return

    else:
        try:
            old_instance = Realty.objects.get(id=instance.id)

        except Realty.DoesNotExist:
            return

        old_status = old_instance.realty_status
        new_status = instance.realty_status

        old_is_deleted = old_instance.is_deleted
        new_is_deleted = instance.is_deleted

        if old_is_deleted != new_is_deleted and new_is_deleted is True:
            create_notification(instance, DELETED_CODE)
            Schedule.objects.filter(
                func='realty.tasks.expire_realty', args=instance.id
            ).delete()
            logger.info('объявление %s удалено, владелец уведомлен', instance.id)

        if new_status != old_status:
            if new_status.id == STATUS_ACTIVE_ID:
                instance.published_at = timezone.now()
                instance.save()

                Schedule.objects.create(
                    func='realty.tasks.expire_realty',
                    name=f'Deactivation of Realty #{instance.id}',
                    args=instance.id,
                    schedule_type=Schedule.ONCE,
                    next_run=timezone.now() + MAX_LISTING_DURATION,
                )

            elif old_status and old_status.id == STATUS_ACTIVE_ID:
                instance.published_at = None

                Schedule.objects.filter(
                    func='realty.tasks.expire_realty', args=instance.id
                ).delete()

            logger.info(
                'статус объявления %s: %s --> %s',
                instance.id,
                old_status.status,
                new_status.status,
            )

            if new_status.id == STATUS_ACTIVE_ID:
                create_notification(instance, PUBLISHED_CODE)

            elif new_status.id == STATUS_ON_MODERATION_ID:
                create_notification(instance, ON_MODERATION_CODE)

            elif new_status.id == STATUS_REJECTED_ID:
                if old_status.id == STATUS_ACTIVE_ID:
                    create_notification(instance, BLOCKED_CODE)
                elif old_status.id == STATUS_ON_MODERATION_ID:
                    create_notification(instance, REJECTED_CODE)

            elif new_status.id == STATUS_ARCHIVED_ID:
                if old_status.id == STATUS_ON_MODERATION_ID:
                    create_notification(instance, ARCHIVED_CODE)
