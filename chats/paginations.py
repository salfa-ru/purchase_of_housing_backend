from config import constants
from config.pagination import BasePagination

UNREAD_TOTAL_SCHEMA = {
    'unread_total': {
        'type': 'integer',
        'description': 'Общее количество непрочитанных сообщений '
        'пользователя во всех чатах.',
        'example': 5,
    },
}


class ChatsPagination(BasePagination):
    """Список чатов: в ответе есть общий счетчик непрочитанного."""

    page_size = constants.CHATS_PAGESIZE_DEFAULT
    max_page_size = constants.CHATS_PAGESIZE_MAX
    extra_schema_properties = UNREAD_TOTAL_SCHEMA


class MessagesPagination(BasePagination):
    """Сообщения внутри чата."""

    page_size = constants.MESSAGES_PAGESIZE_DEFAULT
    max_page_size = constants.MESSAGES_PAGESIZE_MAX
