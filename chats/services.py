from django.db.models import Q, OuterRef, Subquery
from rest_framework import exceptions

from chats.models import Message, Blocking, Chat
from chats.serializers import IdsListSerializer
from realty.models import Realty


# Оказалось, несортированный список чатов почти не нужен!
# def get_chats(current_user):
#     """Получение списка чатов текущего пользователя."""
#     queryset = Chat.objects.filter(
#         Q(owner=current_user) | Q(client=current_user)
#     )   # .order_by('-created_at')
#     return queryset


def get_chats_sorted(current_user):
    """
    Retrieves the user's chats, sorted by the date of the last active
    message (sent by or received by the user, and not deleted).
    """

    # Subquery to get the 'created_at' of the last active message.
    last_active_message_date = Message.objects.filter(
        Q(chat=OuterRef('pk')),  # Connects to the outer Chat query.
        Q(user_from=current_user, is_deleted_from=False) |
        Q(user_to=current_user, is_deleted_to=False)
    ).order_by('-created_at').values('created_at')[:1]  # Only get the 'created_at' value.

    # Main queryset: filter chats for the current_user, annotate with
    # the last active message date, and order by that date.
    queryset = Chat.objects.filter(
        Q(owner=current_user) | Q(client=current_user)
    ).annotate(
        last_message_created_at=Subquery(last_active_message_date)
    ).order_by('-last_message_created_at')  # Descending for most recent first.

    return queryset


def get_chat_by_chat_id(user, chat_id):
    """Получение чата по chat_id"""
    chat = Chat.objects.filter(
        Q(owner=user) | Q(client=user)
    ).filter(chat_id=chat_id).first()

    if not chat:
        msg = f'Чат {chat_id} у текущего пользователя не найден'
        raise exceptions.NotFound(detail=msg)

    return chat


def get_realty_by_realty_id(realty_id):
    """Получение объявления по realty_id"""
    realty = Realty.objects.filter(id=realty_id).first()

    if not realty:
        msg = f'Объявление #{realty_id} не найдено'
        raise exceptions.NotFound(detail=msg)

    return realty


def get_chats_by_ids(current_user, data):
    """Получение списка чатов по id из запроса и проверка прав доступа"""
    serializer = IdsListSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    chat_ids = serializer.validated_data.get('chat_ids')  # Изменено с 'ids' на 'chat_ids'

    chats = Chat.objects.filter(
        Q(chat_id__in=chat_ids) & (Q(owner=current_user) | Q(client=current_user))
    )

    queryset_ids = [item.chat_id for item in chats]
    diff = set(chat_ids) - set(queryset_ids)
    if diff:
        msg = f'Чаты {diff} не найдены или вы не являетесь их участником'
        raise exceptions.NotFound(detail=msg)
    return chats


def check_blocking(user_from, user_to):
    """Проверяет, существует ли блокировка между пользователями.
    Важно проверять именно направление блокировки! """
    is_blocked_by_other = Blocking.objects.filter(user_who=user_to, user_whom=user_from).exists()
    if is_blocked_by_other:
        raise exceptions.PermissionDenied(detail="Пользователь вас заблокировал, вы не можете ему писать")
    is_blocked_by_yourself = Blocking.objects.filter(user_who=user_from, user_whom=user_to).exists()
    if is_blocked_by_yourself:
        raise exceptions.PermissionDenied(detail="Вы заблокировали этого пользователя и не можете ему писать")


def create_message(user_from, message_text, realty_id=None, chat_id=None):
    """Универсальная функция создания сообщения"""
    if chat_id is not None:
        chat = get_chat_by_chat_id(user_from, chat_id)
        user_to = chat.owner if chat.client == user_from else chat.client
        check_blocking(user_from, user_to)
    elif realty_id is not None:
        realty = get_realty_by_realty_id(realty_id)
        user_to = realty.owner

        if user_from == user_to:
            raise exceptions.ValidationError("Вы не можете отправить сообщение самому себе.")

        check_blocking(user_from, user_to)

        chat, created = Chat.objects.get_or_create(
            realty=realty,
            owner=realty.owner,
            client=user_from
        )

    else:
        raise ValueError("Должен быть указан либо chat_id, либо realty_id")

    message = Message.objects.create(
        chat=chat,
        user_from=user_from,
        user_to=user_to,
        message=message_text,
    )
    return message
