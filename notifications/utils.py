import logging

from rest_framework import exceptions

from notifications.models import Notification, NotificationTemplate
from notifications.push import send_push
from notifications.serializers import IdsNotifListSerializer

logger = logging.getLogger(__name__)


def get_queryset_by_ids(user, data):
    """Получение списка уведомлений по данным из запроса,
    включает валидацию данных в запросе"""
    serializer = IdsNotifListSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    ids = serializer.validated_data.get('ids')
    queryset = Notification.objects.filter(user_to=user).filter(id__in=ids).all()
    queryset_ids = [item.id for item in queryset]
    diff = set(ids) - set(queryset_ids)
    if diff:
        msg = f'Notifications {diff} not found'
        raise exceptions.NotFound(detail=msg)
    return queryset, ids


def create_notification(realty, notification_type: str, user_to=None):
    """Создает уведомление и отправляет пуш."""
    user_to = user_to or realty.owner

    try:
        template = NotificationTemplate.objects.get(code=notification_type)
    except NotificationTemplate.DoesNotExist:
        logger.error(
            'уведомление %r не создано: нет шаблона с таким кодом', notification_type
        )
        return None

    notification = Notification.objects.create(
        template=template,
        user_to=user_to,
        realty=realty,
    )

    logger.info(
        'уведомление %r создано: пользователь=%s объявление=%s',
        notification_type,
        user_to.id,
        realty.id,
    )

    send_push(
        user_to,
        title=template.part1,
        body=template.part2 or '',
        data={'notification_id': notification.id, 'realty_id': realty.id},
    )

    return notification
