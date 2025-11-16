from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.helpers import forced_singular_serializer
from rest_framework import generics, permissions, viewsets, views, status  # <-- YYY --- realty_удаление v1
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from config import constants
from realty.pagination import LimitRealtyPagination, MyRealtyPagination, PaginatedResponseSerializer
from realty_addresses import models as realty_addresses_models
from realty_values import models as realty_values_models
from realty_displays.models import DisplayFullInfo, DisplayInSearch
from realty_displays.utils import increment_counter
from realty import models as realty_models
from realty.serializers import serializers_realty as realty_serializers
from realty.serializers import serializers_rent as rent_serializers
from realty.serializers import serializers_sale as sale_serializers
from realty.serializers import serializers_common as common_serializers
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


@extend_schema(tags=["Управление объявлениями о продаже недвижимости"])
@extend_schema_view(
    partial_update=extend_schema(
        summary='Частичное изменение объявления о продаже недвижимости.',
    ),
    # retrieve=extend_schema(
    #     summary=('Просмотр информации объявления о продаже по id записи.'),
    # ),
    create=extend_schema(
        summary='Создание объявления о продаже недвижимости.',
    ),
    # list=extend_schema(
    #     summary=('Просмотр списка объявлений о продаже недвижимости.'),
    # ),
)
class SaleViewSet(BaseViewSet):
    """Sale Viewset."""

    queryset = realty_models.Sale.objects.all()
    http_method_names = ['post', 'patch']

    def get_serializer_class(self):
        # if self.action in ('list', 'retrieve'):
        #     return sale_serializers.SaleReadSerializer
        return sale_serializers.SaleCreateSerializer


@extend_schema(tags=["Управление объявлениями об аренде недвижимости"])
@extend_schema_view(
    partial_update=extend_schema(
        summary='Частичное изменение объявления об аренде недвижимости.',
    ),
    # retrieve=extend_schema(
    #     summary=('Просмотр информации объявления об аренде по id записи.'),
    # ),
    create=extend_schema(
        summary='Создание объявления об аренде недвижимости.',
    ),
    # list=extend_schema(
    #     summary=('Просмотр списка объявлений об аренде недвижимости.'),
    # ),
)
class RentViewSet(BaseViewSet):
    """Rent Viewset."""

    queryset = realty_models.Rent.objects.all()
    http_method_names = ['post', 'patch']

    def get_serializer_class(self):
        # if self.action in ('list', 'retrieve'):
        #     return rent_serializers.RentReadSerializer
        return rent_serializers.RentCreateSerializer

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
    pagination_class = LimitOffsetPagination
    pagination_class.default_limit = 3

    # TODO найти решение без пагинации. Требуется вывод последних 3х объектов.
    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS,
        is_deleted=False,
        owner__is_deleted=False  # <-- YYY --- realty_удаление v1
    ).order_by('-published_at')


...


@extend_schema(
    summary='Получение списка всех объявлений. Доступна фильтрация. '
            'Есть пагинация по 10 объектов.')
class RealtyListView(generics.ListAPIView):
    """Viewing Realty objects queryset."""

    # УБРАНО В ПОЛЬЗУ QUERY SET при удалении объявлений
    # queryset = realty_models.Realty.objects.all().filter(
    #     realty_status__status=constants.ADVERTISMENT_STATUS
    # )  # .order_by('-published_at')

    serializer_class = realty_serializers.ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter

    def get_queryset(self):  # <-- YYY --- Переопределяем get_queryset для фильтрации
        return realty_models.Realty.objects.filter(
            realty_status__status=constants.ADVERTISMENT_STATUS,
            is_deleted=False,
            owner__is_deleted=False  # Показывать только объявления активных владельцев
        ).order_by('-published_at')

    def list(self, request, *args, **kwargs):
        """ Запуск увеличения счетчика показа в поиске с защитой от накрутки."""

        response = super().list(request, *args, **kwargs)
        realty_ids = [realty_data['id'] for realty_data in response.data['results']]
        realties = realty_models.Realty.objects.filter(id__in=realty_ids)

        for realty_data in response.data['results']:
            realty = realties.get(id=realty_data['id'])

            # Увеличиваем счетчик для поиска
            increment_counter(
                request, realty, DisplayInSearch,
                constants.COUNTER_VIEW_IN_SEARCH_MIN_TIME_INTERVAL,
                "DisplayInSearch_time")

        return response


@extend_schema(
    summary='Получение объявления по его id')
class RealtyDetailView(generics.RetrieveAPIView):
    """Viewing Realty object by <id>."""

    # Переопределено для realty_удаление v1
    # queryset = realty_models.Realty.objects.all().filter(
    #     realty_status__status=constants.ADVERTISMENT_STATUS
    # )
    serializer_class = realty_serializers.RealtyBaseSerializer

    def get_queryset(self):  # <-- YYY --- Переопределяем get_queryset для фильтрации
        return realty_models.Realty.objects.filter(
            #  Отдаю ВСЕ объявления, важно чтобы Фронт фильтровал
            #  и не показывал те, что смотреть нельзя!
            #  realty_status__status=constants.ADVERTISMENT_STATUS,
            is_deleted=False,
            owner__is_deleted=False  # Показывать только объявления активных владельцев
        )

    def retrieve(self, request, *args, **kwargs):
        """ Увеличение счетчика полных просмотров """

        realty = self.get_object()

        # Добавлено, что счетчик работает только на активных объявлениях!
        if realty.realty_status.status != constants.ADVERTISMENT_STATUS:
            return super().retrieve(request, *args, **kwargs)

        # Увеличиваем счетчик, передавая нужные параметры
        increment_counter(request, realty, DisplayFullInfo,
                          constants.COUNTER_FULL_VIEW_MIN_TIME_INTERVAL,
                          "DisplayFullInfo_time",
                          timezone.now().date())

        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    summary='Количество найденных объявлений по фильтрам',
    responses=forced_singular_serializer(
        common_serializers.CountRealtySerializer)
)
class RealtyCountView(generics.ListAPIView):
    """Endpoint to get the count of filtered realty objects."""

    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS,
        is_deleted=False,
        owner__is_deleted=False  # Показывать только объявления активных владельцев
    )
    serializer_class = common_serializers.CountRealtySerializer
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
    serializer_class = common_serializers.RealtyOwnerDataSerializer


@extend_schema(
    summary='Получение контактов владельца объявления')
class RealtyOwnerContactsView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner contacts."""

    queryset = realty_models.Realty.objects.all()
    serializer_class = common_serializers.RealtyOwnerContactsSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Показ всех объявлений пользователя в ЛК - со счетчиками и статусом.',
    parameters=[
        OpenApiParameter(
            name='page_size',
            type=int,
            description=(
                f'Количество объявлений на странице (по умолчанию '
                f'{constants.MY_REALTY_PAGESIZE_DEFAULT}, максимум '
                f'{constants.MY_REALTY_PAGESIZE_MAX})'
            ),
            required=False
        ),
        OpenApiParameter(
            name='page',
            type=int,
            description='Номер страницы',
            required=False
        )
    ],
    responses={200: PaginatedResponseSerializer}
)
class RealtyLKListView(generics.ListAPIView):
    """
    <p> Возвращает список объявлений с пагинацией, по умолчанию - 10 объявлений на странице.<br>
    <h3> Структура ответа: </h3>
    <ul>
    <li> <b>count:</b> общее количество объявлений
    <li> <b>page_size:</b> количество объявлений на странице
    <li> <b>pages_total:</b> общее количество страниц
    <li> <b>current_page:</b> номер текущей страницы
    <li> <b>next:</b> ссылка на следующую страницу
    <li> <b>previous:</b> ссылка на предыдущую страницу
    <li> <b>results:</b> массив объявлений </p>"""

    serializer_class = common_serializers.RealtyLKSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MyRealtyPagination

    def get_queryset(self):
        return (
            realty_models.Realty.objects
            .filter(owner_id=self.request.user,
                    is_deleted=False,
                    owner__is_deleted=False  # <-- YYY --- realty_удаление v1
                    )
            .order_by('-published_at')
        )


...


@extend_schema(
    summary='Изменение статуса объявления (может только владелец объявления) .')
class ChangeStatusUpdateAPIView(generics.UpdateAPIView):
    """Endpoint for change status in realty"""
    queryset = realty_models.Realty.objects.all()
    serializer_class = common_serializers.RealtyStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save()


@extend_schema(
    summary='получение данных для фронта.')
class RealtyFilterOptionsView(views.APIView):
    """
    API для получения всех возможных значений фильтров.
    """

    def get(self, request, *args, **kwargs):
        # Получаем данные
        data = {
            "realty_type": [{"id": rt.id, "type": rt.type} for rt in
                            realty_values_models.RealtyType.objects.all()
                            ],
            "address": {
                "street": {
                    "zone": [
                        {"id": bt.id, "name": bt.name} for bt in
                        realty_addresses_models.Zone.objects.all()
                    ],
                    "district": [
                        {"id": bt.id, "name": bt.name} for bt in
                        realty_addresses_models.District.objects.all()
                    ],
                    "city": [
                        {"id": bt.id, "name": bt.name} for bt in
                        realty_addresses_models.City.objects.all()
                    ],

                },
                "metro": [
                    {"id": bt.id, "name": bt.name, "name_full": bt.name_full, "color": bt.line.color} for bt in
                    realty_addresses_models.Metro.objects.all()
                ]
            },

            "about_building": {
                "type": [{"id": bt.id, "type": bt.type} for bt in
                         realty_values_models.BuildingType.objects.all()
                         ]
            },
            "about_apartment": {"rooms_number": [
                {"id": apt.id, "number_of_rooms": apt.number_of_rooms, }
                for apt in realty_values_models.RoomsNumber.objects.all()
            ]},
            "common_characteristics": {
                "repair_types": [{"id": rt.id, "type": rt.type} for rt in
                                 realty_values_models.RepairType.objects.all()
                                 ],
                "bathroom_types": [{"id": bt.id, "type": bt.type} for bt in
                                   realty_values_models.BathroomType.objects.all()],
            },
            "owner_type": {
                "trade_participant": [
                    {"id": apt.id, "participant": apt.participant, }
                    for apt in realty_values_models.TradeParticipant.objects.all()
                ]
            },
            "communication_method": [
                {"id": apt.id, "method": apt.method, }
                for apt in realty_values_models.CommunicationMethod.objects.all()
            ],
            "realty_status": {
                "realty_adv_status": [
                    {"id": apt.id, "status": apt.status, }
                    for apt in realty_values_models.RealtyAdvStatus.objects.all()
                ]
            },

            "sales_parameters": {
                "housing_type": [
                    {"id": apt.id, "type": apt.type}
                    for apt in realty_values_models.HousingType.objects.all()
                ],
                "sale_type": [
                    {"id": apt.id, "type": apt.type}
                    for apt in realty_values_models.SaleType.objects.all()
                ]
            },
            "rent": {
                "lease_payments": {
                    "counters_payment": {
                        "trade_participant": [
                            {"id": apt.id, "participant": apt.participant, }
                            for apt in realty_values_models.TradeParticipant.objects.all()
                        ]
                    },
                    "communal_payment": {
                        "trade_participant": [
                            {"id": apt.id, "participant": apt.participant, }
                            for apt in realty_values_models.TradeParticipant.objects.all()
                        ]
                    }
                }
            }
        }
        return Response(data)


@extend_schema(
    summary='Удаление объявление (soft delete)')  # <-- YYY --- Добавлен эндпоинт soft delete - realty_удаление v1
class RealtyDeleteView(generics.DestroyAPIView):
    queryset = realty_models.Realty.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {"detail": "У вас нет прав на удаление этого объявления."},
                status=status.HTTP_403_FORBIDDEN
            )

        if instance.is_deleted:  # <-- YYY --- Проверка на то, что объявление уже удалено
            return Response(
                {"detail": "Объявление уже удалено."},
                status=status.HTTP_400_BAD_REQUEST  # <-- YYY --- realty_удаление v1
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
