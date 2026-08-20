# chats/paginations.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from config.pagination import StrictPageSizeMixin


class ConfigurablePagination(StrictPageSizeMixin, PageNumberPagination):
    """
    Custom pagination class that allows configuring page size and max page size
    based on provided parameters.
    """

    page_size_query_param = 'page_size'  # Parameter to control page size
    page_query_param = 'page'  # Standard page parameter

    def __init__(
        self, pagesize_default=10, pagesize_max=50, pagination_config_name='ITEMS'
    ):
        """
        Initializes the pagination with custom settings.

        Args:
            pagesize_default: Default page size.
            pagesize_max: Maximum allowed page size.
            pagination_config_name:  String for error/documentation messages (e.g., "CHATS").
        """
        super().__init__()
        self.page_size = pagesize_default
        self.max_page_size = pagesize_max
        self.pagination_config_name = pagination_config_name
        self.page_size_query_description = (
            f'Количество объектов на странице. '
            f'По умолчанию {pagesize_default}, '
            f'максимум {pagesize_max}. '
            f'({pagination_config_name}_PAGESIZE_MAX)'
        )

    def get_paginated_response(self, data):
        """
        Constructs the paginated response with custom fields.
        """
        return Response(
            {
                'count': self.page.paginator.count,
                'page_size': self.get_page_size(self.request),
                'pages_total': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
            }
        )

    def get_paginated_response_schema(self, schema):
        """For openapi documentation."""
        return {
            'type': 'object',
            'properties': {
                # --- ДОБАВЛЕНО ЭТО ПОЛЕ ---
                'unread_total': {
                    'type': 'integer',
                    'description': 'Общее количество непрочитанных сообщений для пользователя во всех чатах.',
                    'example': 5,
                },
                # --- КОНЕЦ ДОБАВЛЕНИЯ ---
                'count': {
                    'type': 'integer',
                    'example': 123,
                },
                'page_size': {
                    'type': 'integer',
                    'example': 10,
                },
                'pages_total': {
                    'type': 'integer',
                    'example': 13,
                },
                'current_page': {
                    'type': 'integer',
                    'example': 1,
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                },
                'results': schema,
            },
        }
