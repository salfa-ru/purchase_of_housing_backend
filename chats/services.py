from django.db.models import Q
from rest_framework import exceptions

from chats.models import Chat, Blocking
from chats.serializers import IdSerializer, IdsListSerializer
from realty.models import Realty


def get_chats(current_user):
    """Получение списка переписок текущего пользователя
    (не удаленных, без дубликатов)"""
    queryset = Chat.objects.filter(
        Q(user_from=current_user, is_deleted_from=False) |
        Q(user_to=current_user, is_deleted_to=False)
    ).order_by('-datetime').all()

    unique_pairs = []
    filtered_queryset = []
    for chat in queryset:
        user = chat.user_from if chat.user_from != current_user else chat.user_to
        if (user, chat.realty) not in unique_pairs:
            unique_pairs.append((user, chat.realty))
            filtered_queryset.append(chat)

    return filtered_queryset


def get_chat_by_id(user, data):
    """Получение сообщения по id из запроса,
    включает валидацию данных в запросе
    и проверку существования такого чата у текущего пользователя"""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    chat_id = serializer.validated_data.get('id_from')
    chat = Chat.objects.filter(
        Q(user_from=user) | Q(user_to=user)
    ).filter(id=chat_id).first()

    if not chat:
        msg = f'Chat with pk={chat_id} not found for current user'
        raise exceptions.NotFound(detail=msg)

    return chat


def get_realty_by_id(data):
    """Получение объявления по id из запроса,
    включает валидацию данных в запросе
    и проверку существования такого чата у текущего пользователя"""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    realty_id = serializer.validated_data.get('id_from')
    realty = Realty.objects.filter(id=realty_id).first()

    if not realty:
        msg = f'Realty with pk={realty_id} not found'
        raise exceptions.NotFound(detail=msg)

    return realty


def get_chats_by_ids(current_user, data):
    """Получение списка сообщений по данным из запроса,
    включает валидацию данных в запросе"""
    serializer = IdsListSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    ids = serializer.validated_data.get('ids')
    chats = Chat.objects.filter(
        Q(user_from=current_user) | Q(user_to=current_user)
    ).filter(id__in=ids).all()

    queryset_ids = [item.id for item in chats]
    diff = set(ids) - set(queryset_ids)
    if diff:
        msg = f'Chat {diff} not found'
        raise exceptions.NotFound(detail=msg)
    return chats, ids


def multiple_delete_chats(current_user, chats):
    """Удаление всех сообщений в цепочках переданных переписок."""

    for chat in chats:
        second_user = chat.user_from if chat.user_from != current_user else chat.user_to
        realty = chat.realty
        Chat.objects.filter(
            user_from=current_user,
            is_deleted_from=False,
            user_to=second_user,
            realty=realty
        ).update(is_deleted_from=True)
        Chat.objects.filter(
            user_from=second_user,
            user_to=current_user,
            is_deleted_to=False,
            realty=realty
        ).update(is_deleted_to=True)


def create_blocking(current_user, chats):
    """Создание записей о блокировке."""

    blocking_users = set()
    for chat in chats:
        user = chat.user_from if chat.user_from != current_user else chat.user_to
        if not Blocking.objects.filter(user_who=current_user,
                                       user_whom=user).exists():
            blocking_users.add(user)

    blocking_list = Blocking.objects.bulk_create(
        [Blocking(user_who=current_user, user_whom=user) for user in
         blocking_users]
    )

    return blocking_list
