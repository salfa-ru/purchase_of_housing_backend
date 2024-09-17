from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from config import constants
from .models import Realty
from .pagination import LimitRealtyPagination
from .serializers import (ShortRealtySerializer, RealtyBaseSerializer, CountRealtySerializer)
from .filters import RealtyFilter


@extend_schema(
    summary='Получение списка последних 3х объявлений. Доступна фильтрация.')
class LastRealtyListView(generics.ListAPIView):
    """Viewing last 3 Realty objects."""

    serializer_class = ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter
    pagination_class = LimitOffsetPagination
    pagination_class.default_limit = 3
    # TODO найти решение без пагинации. Требуется вывод последних 3х объектов.
    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        ).order_by('-published_at')


@extend_schema(
    summary='Получение списка всех объявлений. Доступна фильтрация. '
    'Есть пагинация по 10 объектов.')
class RealtyListView(generics.ListAPIView):
    """Viewing Realty objects queryset."""

    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        ).order_by('-published_at')
    serializer_class = ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter


@extend_schema(
    summary='Получение объявления по его id')
class RealtyDetailView(generics.RetrieveAPIView):
    """Viewing Realty object by <id>."""

    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        )
    serializer_class = RealtyBaseSerializer


@extend_schema(
    summary='Количество найденных объявлений по фильтрам',
    )
class RealtyCountView(generics.ListAPIView):
    """Endpoint to get the count of filtered realty objects."""

    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    )
    serializer_class = CountRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.count()
        return Response({'count': count})
