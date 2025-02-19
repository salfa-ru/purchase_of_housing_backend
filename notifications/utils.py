from rest_framework import exceptions

from notifications.models import Notification, NotificationTemplate
from notifications.serializers import IdsNotifListSerializer


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


def create_notification(realty, notification_type: str):
    """ Отправка Уведомления владельцу объявления """

    # находим тип уведомления
    template = NotificationTemplate.objects.get(code=notification_type)

    # создаем Уведомление
    Notification.objects.create(
        template=template,
        user_to=realty.owner,
        realty=realty,
    )

    print(f"DEBUG - notifications/utils.py - create_notification():")
    print(f"        Пользователю {realty.owner} отправлено оповещение '{notification_type}' об объявлении #{realty.id}")
