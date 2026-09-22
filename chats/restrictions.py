"""Единая точка правды о том, можно ли писать в чат."""

from chats.models import Blocking

# Статус объявления «В архиве» (см. фикстуру realty_values.realtyadvstatus).
# Сверяемся по названию, как в realty/forms.py и в проверке переходов
# статуса: id статусов зависят от того, как наполнялась база.
ARCHIVED_STATUS_NAME = 'В архиве'

SEND_DENIED_USER_DELETED = 'Пользователь удален. Отправка сообщений невозможна.'
SEND_DENIED_BLOCKED_BY_OTHER = 'Пользователь вас заблокировал, вы не можете ему писать'
SEND_DENIED_BLOCKED_BY_YOU = (
    'Вы заблокировали этого пользователя и не можете ему писать'
)
SEND_DENIED_REALTY_DELETED = 'Объявление удалено'
SEND_DENIED_REALTY_ARCHIVED = 'Невозможно отправить сообщение в архивное объявление'


def is_archived(realty):
    """Объявление в архиве."""
    return getattr(realty.realty_status, 'status', None) == ARCHIVED_STATUS_NAME


def get_send_restriction(user, chat=None, realty=None):
    """
    Возвращает причину, по которой пользователь не может писать в чат,
    или None, если писать можно."""
    other_user = None

    if chat is not None:
        realty = chat.realty
        other_user = chat.owner if chat.client == user else chat.client
    elif realty is not None:
        other_user = realty.owner

    if other_user is not None and other_user != user:
        if other_user.is_deleted:
            return SEND_DENIED_USER_DELETED
        if Blocking.objects.filter(user_who=other_user, user_whom=user).exists():
            return SEND_DENIED_BLOCKED_BY_OTHER
        if Blocking.objects.filter(user_who=user, user_whom=other_user).exists():
            return SEND_DENIED_BLOCKED_BY_YOU

    if realty is None:
        return None

    if realty.is_deleted:
        return SEND_DENIED_REALTY_DELETED

    if is_archived(realty):
        return SEND_DENIED_REALTY_ARCHIVED

    return None
