from collections import OrderedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response

from config import constants
from realty.serializers import serializers_common as common_serializers


class LimitRealtyPagination(PageNumberPagination):
    """Custom pagination for Realty queryset."""

    page_size_query_param = None
    page_size = 10


class LatestRealtyPagination(LimitOffsetPagination):
    """LimitOffset-пагинация для /api/realty/latest/ со строгой валидацией."""

    default_limit = constants.LATEST_REALTY_LIMIT_DEFAULT
    max_limit = constants.LATEST_REALTY_LIMIT_MAX

    def get_limit(self, request):
        if self.limit_query_param not in request.query_params:
            return self.default_limit
        raw = request.query_params[self.limit_query_param]
        try:
            limit = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({'limit': 'Должно быть положительным целым числом.'})
        if limit <= 0:
            raise ValidationError({'limit': 'Должно быть положительным целым числом.'})
        return min(limit, self.max_limit)

    def get_offset(self, request):
        if self.offset_query_param not in request.query_params:
            return 0
        raw = request.query_params[self.offset_query_param]
        try:
            offset = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({'offset': 'Должно быть целым числом >= 0.'})
        if offset < 0:
            raise ValidationError({'offset': 'Должно быть целым числом >= 0.'})
        return offset


class PaginatedResponseSerializer(serializers.Serializer):
    """Сериализатор для корректного отображения пагинации в Swagger."""

    count = serializers.IntegerField(help_text='Общее количество объявлений')
    page_size = serializers.IntegerField(help_text='Количество объявлений на странице')
    pages_total = serializers.IntegerField(help_text='Общее количество страниц')
    current_page = serializers.IntegerField(help_text='Номер текущей страницы')
    next = serializers.URLField(
        help_text='Ссылка на следующую страницу', allow_null=True
    )
    previous = serializers.URLField(
        help_text='Ссылка на предыдущую страницу', allow_null=True
    )
    results = common_serializers.RealtyLKSerializer(many=True)


class MyRealtyPagination(PageNumberPagination):
    """Custom pagination for my Realty queryset для ЛИЧНОГО КАБИНЕТА."""

    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        def_page_size = constants.MY_REALTY_PAGESIZE_DEFAULT
        max_page_size = constants.MY_REALTY_PAGESIZE_MAX

        if not self.page_size_query_param:
            return def_page_size

        try:
            page_size = int(
                request.query_params.get(self.page_size_query_param, def_page_size)
            )
            if page_size > max_page_size:
                raise ValidationError(
                    f'Максимальное количество объявлений на странице: {max_page_size}'
                )
            return page_size
        except ValueError:
            return def_page_size

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ('count', self.page.paginator.count),
                    ('page_size', self.get_page_size(self.request)),
                    ('pages_total', self.page.paginator.num_pages),
                    ('current_page', self.page.number),
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('results', data),
                ]
            )
        )
