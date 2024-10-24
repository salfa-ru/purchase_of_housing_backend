from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema  # , OpenApiParameter
from drf_spectacular.helpers import forced_singular_serializer
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
# from rest_framework.pagination import LimitOffsetPagination

from config import constants
from realty.pagination import LimitRealtyPagination
from realty_displays.models import DisplayFullInfo, DisplayInSearch
from realty_displays.utils import increment_counter
from realty import models as realty_models
from realty import serializers as realty_serializers
from realty.filters import RealtyFilter


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset."""

    http_method_names = ["post"]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class RealtyBaseViewSet(BaseViewSet):
    """Realty Base viewset.
    Viewing, creating, editing, removal."""

    queryset = realty_models.Realty.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.RealtyCreateSerializer
        return realty_serializers.RealtyBaseSerializer


class SaleViewSet(BaseViewSet):
    """Sale Viewset."""

    queryset = realty_models.Sale.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.SaleCreateSerializer
        #     elif self.action == "update" or self.action == "partial_update":
        #         return realty_serializers.SaleUpdateSerializer
        #     elif self.action == "destroy":
        #         return realty_serializers.SaleDeleteSerializer
        return realty_serializers.SaleReadSerializer


class RentViewSet(BaseViewSet):
    """Rent Viewset."""

    queryset = realty_models.Rent.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.RentCreateSerializer
        #     elif self.action == "update" or self.action == "partial_update":
        #         return realty_serializers.RentUpdateSerializer
        #     elif self.action == "destroy":
        #         return realty_serializers.RentDeleteSerializer
        return realty_serializers.RentReadSerializer

    # на будущее для доб в избранное
    # @staticmethod
    # def create_obj(request, pk, serializers):
    #     user = request.user
    #     realty_data = {
    #         "owner": user.id,
    #         "realty_id": pk,
    #     }
    #     serializer = serializers(data=realty_data,
    # context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Получение списка последних 3х объявлений. Доступна фильтрация.')
class LastRealtyListView(generics.ListAPIView):
    """Viewing last 3 Realty objects."""

    serializer_class = realty_serializers.ShortRealtySerializer
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
    queryset = realty_models.Realty.objects.filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    ).order_by('-published_at')[:3]


@extend_schema(
    summary='Получение списка всех объявлений. Доступна фильтрация. '
    'Есть пагинация по 10 объектов.')
class RealtyListView(generics.ListAPIView):
    """Viewing Realty objects queryset."""

    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        ).order_by('-published_at')
    serializer_class = realty_serializers.ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter

    def list(self, request, *args, **kwargs):

        """ Запуск увеличения счетчика проказа в поиске с защитой от накрутки."""

        # Call the original list method to get the paginated response
        response = super().list(request, *args, **kwargs)
        realty_ids = [realty_data['id'] for realty_data in response.data['results']]
        realties = realty_models.Realty.objects.filter(id__in=realty_ids)

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

    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
        )
    serializer_class = realty_serializers.RealtyBaseSerializer

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
    responses=forced_singular_serializer(realty_serializers.CountRealtySerializer)
    )
class RealtyCountView(generics.ListAPIView):
    """Endpoint to get the count of filtered realty objects."""

    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    )
    serializer_class = realty_serializers.CountRealtySerializer
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

    queryset = realty_models.Realty.objects.all()
    serializer_class = realty_serializers.RealtyOwnerDataSerializer


@extend_schema(
    summary='Получение контактов владельца объявления')
class RealtyOwnerContactsView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner contacts."""

    queryset = realty_models.Realty.objects.all()
    serializer_class = realty_serializers.RealtyOwnerContactsSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Показ всех объявлений пользователя в ЛК - со счетчиками и статусом.')
class RealtyLKListView(generics.ListAPIView):
    """Viewing Realty objects queryset with view counts."""

    serializer_class = realty_serializers.RealtyLKSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner = self.request.user
        queryset = realty_models.Realty.objects.filter(owner_id=owner).order_by('-published_at')

        return queryset


class ChangeStatusUpdateAPIView(generics.UpdateAPIView):
    """Endpoint for change status in realty"""
    queryset = realty_models.Realty.objects.all()
    serializer_class = realty_serializers.RealtyStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save()

