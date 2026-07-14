from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from config import constants


class FavoritePagination(PageNumberPagination):
    """Пагинатор для избранного пользователя."""

    page_size_query_param = None
    page_size = constants.FAVORITES_PAGESIZE_DEFAULT

    def get_paginated_response(self, data):
        """
        Собирает ответ страницы с полями навигации.
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
        """Описание ответа для документации OpenAPI."""
        return {
            'type': 'object',
            'properties': {
                'unviewed_count': {
                    'type': 'integer',
                    'example': 2,
                },
                'count': {
                    'type': 'integer',
                    'example': 9,
                },
                'page_size': {
                    'type': 'integer',
                    'example': constants.FAVORITES_PAGESIZE_DEFAULT,
                },
                'pages_total': {
                    'type': 'integer',
                    'example': 3,
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
