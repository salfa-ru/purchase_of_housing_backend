from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from config import constants
from .models import Realty
from .pagination import LimitRealtyPagination
from .serializers import (ShortRealtySerializer, RealtyBaseSerializer)
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
    serializer_class = RealtyBaseSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter


@extend_schema(
    summary='Получение объявления по его id')
class RealtyDetailView(generics.RetrieveAPIView):
    """Viewing Realty object by <id>."""

    queryset = Realty.objects.all()
    serializer_class = RealtyBaseSerializer
