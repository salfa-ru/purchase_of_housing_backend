from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.response import Response
# from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema  # , OpenApiParameter
from drf_spectacular.helpers import forced_singular_serializer

from config import constants
from realty_displays.models import DisplayFullInfo, DisplayInSearch
from realty_displays.utils import increment_counter
from .models import Realty
from .pagination import LimitRealtyPagination
from .serializers import (ShortRealtySerializer, RealtyBaseSerializer,
                          CountRealtySerializer, RealtyOwnerDataSerializer,
                          RealtyOwnerContactsSerializer, RealtyLKSerializer)
from .filters import RealtyFilter


@extend_schema(
    summary='Получение списка последних 3х объявлений. Доступна фильтрация.')
class LastRealtyListView(generics.ListAPIView):
    """Viewing last 3 Realty objects."""

    serializer_class = ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    """
    pagination_class = LimitOffsetPagination
    pagination_class.default_limit = 3
    # TODO найти решение без пагинации. Требуется вывод последних 3х объектов.
    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        ).order_by('-published_at')
        """

    # TODO - Как насчет такого решения? Апдейт: заработало после отключения всех строк сверху
    # Работает, в том числе если:
    # - объявлений находится меньше, чем надо показать
    # - если объявлений больше, чем надо показать - показывает 3
    # Да, при возвращении объектов не показывает их количество, как при пагинации

    # Отдаем 3 последних объекта
    queryset = Realty.objects.filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    ).order_by('-published_at')[:3]


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

    def list(self, request, *args, **kwargs):

        """ Запуск увеличения счетчика проказа в поиске с защитой от накрутки."""

        # Call the original list method to get the paginated response
        response = super().list(request, *args, **kwargs)
        realty_ids = [realty_data['id'] for realty_data in response.data['results']]
        realties = Realty.objects.filter(id__in=realty_ids)

        for realty_data in response.data['results']:
            realty = realties.get(id=realty_data['id'])

            # Увеличиваем счетчик для поиска
            increment_counter(request, realty, DisplayInSearch,
                              constants.COUNTER_VIEW_IN_SEARCH_MIN_TIME_INTERVAL,
                              "DisplayInSearch_time")

        return response


@extend_schema(
    summary='Получение объявления по его id')
class RealtyDetailView(generics.RetrieveAPIView):
    """Viewing Realty object by <id>."""

    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        )
    serializer_class = RealtyBaseSerializer

    def retrieve(self, request, *args, **kwargs):

        """ Увеличение счетчика полных просмотров """

        realty = self.get_object()
        # Увеличиваем счетчик, передавая нужные параметры
        increment_counter(request, realty, DisplayFullInfo,
                          constants.COUNTER_FULL_VIEW_MIN_TIME_INTERVAL,
                          "DisplayFullInfo_time",
                          timezone.now().date())

        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    summary='Количество найденных объявлений по фильтрам',
    responses=forced_singular_serializer(CountRealtySerializer)
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


@extend_schema(
    summary='Получение информации о владельце объявления')
class RealtyOwnerDataView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner data."""

    queryset = Realty.objects.all()
    serializer_class = RealtyOwnerDataSerializer


@extend_schema(
    summary='Получение контактов владельца объявления')
class RealtyOwnerContactsView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner contacts."""

    queryset = Realty.objects.all()
    serializer_class = RealtyOwnerContactsSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Показ всех объявлений пользователя в ЛК - со счетчиками и статусом.')
class RealtyLKListView(generics.ListAPIView):
    """Viewing Realty objects queryset with view counts."""

    serializer_class = RealtyLKSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner = self.request.user
        queryset = Realty.objects.filter(owner_id=owner).order_by('-published_at')

        return queryset
