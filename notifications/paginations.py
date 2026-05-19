from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class NotificationPagination(PageNumberPagination):
    """Пагинатор для уведомлений в личном кабинете."""

    page_size_query_param = None
    page_size = 10

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
                'unread_total': {
                    'type': 'integer',
                    'example': 3,
                },
                'count': {
                    'type': 'integer',
                    'example': 18,
                },
                'page_size': {
                    'type': 'integer',
                    'example': 10,
                },
                'pages_total': {
                    'type': 'integer',
                    'example': 2,
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
