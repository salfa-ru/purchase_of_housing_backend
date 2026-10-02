from config import constants
from config.pagination import BasePagination


class FavoritePagination(BasePagination):
    """Избранное пользователя: в ответе есть счетчик непросмотренных."""

    page_size = constants.FAVORITES_PAGESIZE_DEFAULT
    max_page_size = 100
    extra_schema_properties = {
        'unviewed_count': {'type': 'integer', 'example': 2},
    }
