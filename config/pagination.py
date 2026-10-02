from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

PAGE_SIZE_ERROR = 'Должно быть положительным целым числом.'


class StrictPageSizeMixin:
    """Строгая проверка параметра page_size."""

    def get_page_size(self, request):
        if not self.page_size_query_param:
            return self.page_size

        if self.page_size_query_param not in request.query_params:
            return self.page_size

        raw = request.query_params[self.page_size_query_param]
        try:
            page_size = int(raw)
        except (TypeError, ValueError) as err:
            raise ValidationError(
                {self.page_size_query_param: PAGE_SIZE_ERROR}
            ) from err

        if page_size <= 0:
            raise ValidationError({self.page_size_query_param: PAGE_SIZE_ERROR})

        if self.max_page_size and page_size > self.max_page_size:
            raise ValidationError(
                {
                    self.page_size_query_param: (
                        f'Не должно превышать {self.max_page_size}.'
                    )
                }
            )
        return page_size


class BasePagination(StrictPageSizeMixin, PageNumberPagination):
    """Общий вид страницы для всех списков API.

    Приложения наследуются и задают свои размеры страницы, а в
    extra_schema_properties добавляют собственные поля ответа.
    """

    page_size_query_param = 'page_size'
    extra_schema_properties = {}

    def get_paginated_response(self, data):
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
        return {
            'type': 'object',
            'properties': {
                **self.extra_schema_properties,
                'count': {'type': 'integer', 'example': 123},
                'page_size': {'type': 'integer', 'example': self.page_size},
                'pages_total': {'type': 'integer', 'example': 13},
                'current_page': {'type': 'integer', 'example': 1},
                'next': {'type': 'string', 'nullable': True, 'format': 'uri'},
                'previous': {'type': 'string', 'nullable': True, 'format': 'uri'},
                'results': schema,
            },
        }
