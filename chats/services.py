from django.db.models import Q
from rest_framework import exceptions

from chats.models import Message, Blocking
from chats.serializers import IdSerializer, IdsListSerializer
from realty.models import Realty


def get_zhats(current_user):
    """Получение списка переписок текущего пользователя
    (не удаленных, без дубликатов)"""
    queryset = Message.objects.filter(
        Q(user_from=current_user, is_deleted_from=False) |
        Q(user_to=current_user, is_deleted_to=False)
    ).order_by('-datetime').all()

    unique_pairs = []
    filtered_queryset = []
    for zhat in queryset:
        user = zhat.user_from if zhat.user_from != current_user else zhat.user_to
        if (user, zhat.realty) not in unique_pairs:
            unique_pairs.append((user, zhat.realty))
            filtered_queryset.append(zhat)

    return filtered_queryset


def get_zhat_by_id(user, data):
    """Получение сообщения по id из запроса,
    включает валидацию данных в запросе
    и проверку существования такого 4ата у текущего пользователя"""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    zhat_id = serializer.validated_data.get('id_from')
    zhat = Message.objects.filter(
        Q(user_from=user) | Q(user_to=user)
    ).filter(msg_id=zhat_id).first()

    if not zhat:
        msg = f'Zhat with pk={zhat_id} not found for current user'
        raise exceptions.NotFound(detail=msg)

    return zhat


def get_realty_by_id(data):
    """Получение объявления по id из запроса,
    включает валидацию данных в запросе
    и проверку существования такого 4ата у текущего пользователя"""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    realty_id = serializer.validated_data.get('id_from')
    realty = Realty.objects.filter(id=realty_id).first()

    if not realty:
        msg = f'Realty with pk={realty_id} not found'
        raise exceptions.NotFound(detail=msg)

    return realty


def get_zhats_by_ids(current_user, data):
    """Получение списка сообщений по данным из запроса,
    включает валидацию данных в запросе"""
    serializer = IdsListSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    ids = serializer.validated_data.get('ids')
    zhats = Message.objects.filter(
        # иначе позволял "удалять" сообщения, которых не был видно!
        Q(user_from=current_user, is_deleted_from=False) | Q(user_to=current_user, is_deleted_to=False)
    ).filter(msg_id__in=ids).all()

    queryset_ids = [item.msg_id for item in zhats]
    diff = set(ids) - set(queryset_ids)
    if diff:
        msg = f'Сообщения {diff} не найдены'
        raise exceptions.NotFound(detail=msg)
    return zhats, ids


def multiple_delete_zhats(current_user, zhats):
    """Удаление всех сообщений в цепочках переданных переписок."""

    for zhat in zhats:
        second_user = zhat.user_from if zhat.user_from != current_user else zhat.user_to
        realty = zhat.realty
        Message.objects.filter(
            user_from=current_user,
            is_deleted_from=False,
            user_to=second_user,
            realty=realty
        ).update(is_deleted_from=True)
        Message.objects.filter(
            user_from=second_user,
            user_to=current_user,
            is_deleted_to=False,
            realty=realty
        ).update(is_deleted_to=True)


def create_blocking(current_user, zhats):
    """Создание записей о блокировке."""

    blocking_users = set()
    for zhat in zhats:
        user = zhat.user_from if zhat.user_from != current_user else zhat.user_to
        if not Blocking.objects.filter(user_who=current_user,
                                       user_whom=user).exists():
            blocking_users.add(user)

    blocking_list = Blocking.objects.bulk_create(
        [Blocking(user_who=current_user, user_whom=user) for user in
         blocking_users]
    )

    return blocking_list


def remove_blocking(current_user, zhats):
    unblock_users = set()
    for zhat in zhats:
        user = zhat.user_from if zhat.user_from != current_user else zhat.user_to
        unblock_users.add(user)
    unblocking_list = Blocking.objects.filter(user_who=current_user, user_whom__in=unblock_users)
    blocking_count, _ = unblocking_list.delete()

    return blocking_count
