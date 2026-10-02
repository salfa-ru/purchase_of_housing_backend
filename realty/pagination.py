from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

from config import constants
from config.pagination import BasePagination
from realty.serializers import serializers_common as common_serializers


class LimitRealtyPagination(PageNumberPagination):
    """Пагинация списка объявлений."""

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
        except (TypeError, ValueError) as err:
            raise ValidationError(
                {'limit': 'Должно быть положительным целым числом.'}
            ) from err
        if limit <= 0:
            raise ValidationError({'limit': 'Должно быть положительным целым числом.'})
        if limit > self.max_limit:
            raise ValidationError({'limit': f'Не должно превышать {self.max_limit}.'})
        return limit

    def get_offset(self, request):
        if self.offset_query_param not in request.query_params:
            return 0
        raw = request.query_params[self.offset_query_param]
        try:
            offset = int(raw)
        except (TypeError, ValueError) as err:
            raise ValidationError({'offset': 'Должно быть целым числом >= 0.'}) from err
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


class MyRealtyPagination(BasePagination):
    """Мои объявления в личном кабинете."""

    page_size = constants.MY_REALTY_PAGESIZE_DEFAULT
    max_page_size = constants.MY_REALTY_PAGESIZE_MAX
