from rest_framework import exceptions

from notifications.models import Notification
from notifications.serializers import IdsListSerializer


def get_queryset_by_ids(user, data):
    """Получение списка уведомлений по данным из запроса,
    включает валидацию данных в запросе"""
    serializer = IdsListSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    ids = serializer.validated_data.get('ids')
    queryset = Notification.objects.filter(user_to=user).filter(id__in=ids).all()
    queryset_ids = [item.id for item in queryset]
    diff = set(ids) - set(queryset_ids)
    if diff:
        msg = f'Notifications {diff} not found'
        raise exceptions.NotFound(detail=msg)
    return queryset, ids
