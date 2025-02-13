from django.db.models import Q
from rest_framework import exceptions

from chats.models import Message, Blocking, Chat
from chats.serializers import IdSerializer, IdsListSerializer
from realty.models import Realty


def get_chats(current_user):
    """Получение списка чатов текущего пользователя."""
    queryset = Chat.objects.filter(
        Q(owner=current_user) | Q(client=current_user)
    ).order_by('-created_at')
    return queryset


def get_chat_by_id(user, data):
    """Получение чата по id из запроса."""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    chat_id = serializer.validated_data.get('id_from')
    chat = Chat.objects.filter(
        Q(owner=user) | Q(client=user)
    ).filter(chat_id=chat_id).first()

    if not chat:
        msg = f'Чат {chat_id} у текущего пользователя не найден'
        raise exceptions.NotFound(detail=msg)

    return chat


def get_realty_by_id(data):
    """Получение объявления по id из запроса,
    включает валидацию данных в запросе
    и проверку существования такого 4ата у текущего пользователя"""
    serializer = IdSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    realty_id = serializer.validated_data.get('id_from')
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

    chats = Chat.objects.filter(chat_id__in=chat_ids).filter(
        Q(owner=current_user) | Q(client=current_user)
    ).all()

    queryset_ids = [item.chat_id for item in chats]
    diff = set(chat_ids) - set(queryset_ids)
    if diff:
        msg = f'Чаты {diff} не найдены или вы не являетесь их участником'
        raise exceptions.NotFound(detail=msg)
    return chats


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


def check_blocking(user_from, user_to):
    """Проверяет, существует ли блокировка между пользователями"""
    is_blocked_by_other = Blocking.objects.filter(user_who=user_to, user_whom=user_from).exists()
    if is_blocked_by_other:
        raise exceptions.PermissionDenied(detail="Пользователь вас заблокировал, вы не можете ему писать")
    is_blocked_by_yourself = Blocking.objects.filter(user_who=user_from, user_whom=user_to).exists()
    if is_blocked_by_yourself:
        raise exceptions.PermissionDenied(detail="Вы заблокировали этого пользователя и не можете ему писать")


def create_message(user_from, message_text, realty=None, chat=None):
    """Создает новое сообщение, при необходимости создает чат."""
    if chat is None:
        if realty is None:
            raise ValueError("Either 'realty' or 'chat' must be provided.")
        user_to = realty.owner

        # Проверка на self-message
        if user_from == user_to:
            raise exceptions.ValidationError("Вы не можете отправить сообщение самому себе.")

        # Проверка блокировки ДО создания чата
        check_blocking(user_from, user_to)

        chat, created = Chat.objects.get_or_create(
            realty=realty,
            owner=realty.owner,
            client=user_from,
        )
    else:
        other_user = chat.owner if user_from == chat.client else chat.client

        if user_from == other_user:
            raise exceptions.ValidationError("Вы не можете отправить сообщение самому себе.")
        user_to = other_user
        realty = chat.realty

        # Проверка блокировки для существующего чата
        check_blocking(user_from, user_to)

    message = Message.objects.create(
        chat=chat,
        user_from=user_from,
        user_to=user_to,
        message=message_text,
    )
    return message
