from django.db.models import Q

from chats.models import Chat


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
