from django.db.models import Q
from rest_framework import exceptions

from chats.models import Chat
from chats.serializers import IdSerializer


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

    chat_id = serializer.validated_data.get('id')
    chat = Chat.objects.filter(
        Q(user_from=user) | Q(user_to=user)
    ).filter(id=chat_id).first()

    if not chat:
        msg = f'Chat with pk={chat_id} not found for current user'
        raise exceptions.NotFound(detail=msg)

    return chat
