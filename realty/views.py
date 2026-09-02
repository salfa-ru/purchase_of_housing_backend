from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.helpers import forced_singular_serializer
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import (  # <-- YYY --- realty_удаление v1
    generics,
    permissions,
    status,
    views,
    viewsets,
)
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config import constants
from realty import models as realty_models
from realty.filters import CatalogPriceFilter, LatestRealtyFilter, RealtyFilter
from realty.pagination import (
    LatestRealtyPagination,
    LimitRealtyPagination,
    MyRealtyPagination,
    PaginatedResponseSerializer,
)
from realty.serializers import serializers_common as common_serializers
from realty.serializers import serializers_realty as realty_serializers
from realty.serializers import serializers_rent as rent_serializers
from realty.serializers import serializers_sale as sale_serializers
from realty_addresses import models as realty_addresses_models
from realty_displays.models import DisplayFullInfo, DisplayInSearch
from realty_displays.utils import increment_counter
from realty_values import models as realty_values_models

from .models import Realty
from .serializers.serializers_realty import RealtyBaseSerializer


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset."""

    http_method_names = ['post']

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class RealtyBaseViewSet(BaseViewSet):
    """Realty Base viewset.
    Viewing, creating, editing, removal."""

    queryset = realty_models.Realty.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return realty_serializers.RealtyCreateSerializer
        return realty_serializers.RealtyBaseSerializer


@extend_schema(tags=['Недвижимость | Продажа'])
@extend_schema_view(
    create=extend_schema(
        summary='Создание объявления о продаже недвижимости.',
        description='Создаёт новое объявление о продаже недвижимости. '
        'Требуется авторизация. Все обязательные поля должны быть заполнены.',
    ),
    partial_update=extend_schema(
        summary='Частичное изменение объявления о продаже недвижимости.',
        description='Обновляет отдельные поля объявления о продаже. '
        'Доступно только владельцу объявления.',
    ),
    # Если нужно добавить другие методы:
    # list=extend_schema(
    #     summary='Просмотр списка объявлений о продаже',
    #     description='Возвращает список всех объявлений о продаже. Доступна фильтрация.',
    # ),
    # retrieve=extend_schema(
    #     summary='Просмотр объявления о продаже',
    #     description='Возвращает детальную информацию о продаже по id.',
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


@extend_schema(tags=['Недвижимость | Аренда'])
@extend_schema_view(
    create=extend_schema(
        summary='Создание объявления об аренде недвижимости.',
        description='Создаёт новое объявление об аренде недвижимости. '
        'Требуется авторизация. Все обязательные поля должны быть заполнены.',
    ),
    partial_update=extend_schema(
        summary='Частичное изменение объявления об аренде недвижимости.',
        description='Обновляет отдельные поля объявления об аренде. '
        'Доступно только владельцу объявления.',
    ),
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
    tags=['Недвижимость | Основные'],
    summary='Получение списка последних 3 объявлений',
    description='Возвращает последние 3 активных объявления. Доступна фильтрация по trade_type.',
)
class LastRealtyListView(generics.ListAPIView):
    """Viewing last 3 Realty objects."""

    serializer_class = realty_serializers.ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LatestRealtyFilter
    pagination_class = LatestRealtyPagination

    # TODO найти решение без пагинации. Требуется вывод последних 3х объектов.
    queryset = (
        realty_models.Realty.objects.all()
        .filter(
            realty_status__status=constants.ADVERTISMENT_STATUS,
            is_deleted=False,
            owner__is_deleted=False,  # <-- YYY --- realty_удаление v1
        )
        .order_by('-published_at')
    )

    def filter_queryset(self, queryset):
        trade_type = self.request.query_params.get('trade_type')
        if trade_type is not None and not trade_type.strip():
            raise ValidationError(
                {
                    'trade_type': (
                        'Значение не может быть пустым. '
                        'Допустимые значения: sale, rent.'
                    )
                }
            )
        return super().filter_queryset(queryset)


...


@extend_schema(
    tags=['Недвижимость | Основные'],
    summary='Получение списка всех объявлений. Доступна фильтрация. '
    'Есть пагинация по 10 объектов.',
)
class RealtyListView(generics.ListAPIView):
    """Viewing Realty objects queryset."""

    # УБРАНО В ПОЛЬЗУ QUERY SET при удалении объявлений
    # queryset = realty_models.Realty.objects.all().filter(
    #     realty_status__status=constants.ADVERTISMENT_STATUS
    # )  # .order_by('-published_at')

    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter

    def get_serializer_class(self):
        """Анонимам — публичный сериализатор без данных владельца/адреса,
        авторизованным — полный ShortRealtySerializer."""
        if self.request.user and self.request.user.is_authenticated:
            return realty_serializers.ShortRealtySerializer
        return realty_serializers.RealtyPublicSerializer

    def get_queryset(self):  # <-- YYY --- Переопределяем get_queryset для фильтрации
        return realty_models.Realty.objects.filter(
            realty_status__status=constants.ADVERTISMENT_STATUS,
            is_deleted=False,
            owner__is_deleted=False,  # Показывать только объявления активных владельцев
        ).order_by('-published_at')

    def list(self, request, *args, **kwargs):
        """Запуск увеличения счетчика показа в поиске с защитой от накрутки."""

        response = super().list(request, *args, **kwargs)
        realty_ids = [realty_data['id'] for realty_data in response.data['results']]
        realties = realty_models.Realty.objects.filter(id__in=realty_ids)

        for realty_data in response.data['results']:
            realty = realties.get(id=realty_data['id'])

            # Увеличиваем счетчик для поиска
            increment_counter(
                request,
                realty,
                DisplayInSearch,
                constants.COUNTER_VIEW_IN_SEARCH_MIN_TIME_INTERVAL,
                'DisplayInSearch_time',
            )

        return response


@extend_schema(
    tags=['Недвижимость | Основные'], summary='Получение объявления по его id'
)
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
            owner__is_deleted=False,  # Показывать только объявления активных владельцев
        )

    def retrieve(self, request, *args, **kwargs):
        """Увеличение счетчика полных просмотров"""

        realty = self.get_object()

        # Добавлено, что счетчик работает только на активных объявлениях!
        if realty.realty_status.status != constants.ADVERTISMENT_STATUS:
            return super().retrieve(request, *args, **kwargs)

        # Увеличиваем счетчик, передавая нужные параметры
        increment_counter(
            request,
            realty,
            DisplayFullInfo,
            constants.COUNTER_FULL_VIEW_MIN_TIME_INTERVAL,
            'DisplayFullInfo_time',
            timezone.now().date(),
        )

        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=['Недвижимость | Основные'],
    summary='Количество найденных объявлений по фильтрам',
    description='Возвращает количество объявлений, соответствующих переданным фильтрам.',
    responses=forced_singular_serializer(common_serializers.CountRealtySerializer),
)
class RealtyCountView(generics.ListAPIView):
    """Endpoint to get the count of filtered realty objects."""

    queryset = realty_models.Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS,
        is_deleted=False,
        owner__is_deleted=False,  # Показывать только объявления активных владельцев
    )
    serializer_class = common_serializers.CountRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.count()
        return Response({'count': count})


@extend_schema(
    tags=['Недвижимость | Владелец'],
    summary='Получение информации о владельце объявления',
    description='Возвращает данные владельца: id, имя, телефон, QR-код телефона. '
    'Доступно только авторизованным пользователям.',
)
class RealtyOwnerDataView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner data."""

    queryset = realty_models.Realty.objects.all()
    serializer_class = common_serializers.RealtyOwnerDataSerializer


@extend_schema(
    tags=['Недвижимость | Владелец'],
    summary='Получение контактов владельца объявления',
    description='Возвращает контактные данные владельца: телефон и способ связи. '
    'Доступно только авторизованным пользователям.',
)
class RealtyOwnerContactsView(generics.RetrieveAPIView):
    """Endpoint to get realty's owner contacts."""

    queryset = realty_models.Realty.objects.all()
    serializer_class = common_serializers.RealtyOwnerContactsSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    tags=['Недвижимость | Основные'],
    summary='Показ всех объявлений пользователя в ЛК',
    description='Возвращает список объявлений текущего пользователя с пагинацией, '
    'счётчиками просмотров и статусами.',
    parameters=[
        OpenApiParameter(
            name='page_size',
            type=int,
            description=f'Количество объявлений на странице (по умолчанию {constants.MY_REALTY_PAGESIZE_DEFAULT}, максимум {constants.MY_REALTY_PAGESIZE_MAX})',
            required=False,
        ),
        OpenApiParameter(
            name='page',
            type=int,
            description='Номер страницы',
            required=False,
        ),
    ],
    responses={200: PaginatedResponseSerializer},
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
        return realty_models.Realty.objects.filter(
            owner_id=self.request.user,
            is_deleted=False,
            owner__is_deleted=False,  # <-- YYY --- realty_удаление v1
        ).order_by('-published_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


...


@extend_schema(
    tags=['Недвижимость | Управление'],
    summary='Изменение статуса объявления',
    description='Изменяет статус объявления. Доступно только владельцу объявления. '
    'Допустимые переходы: Активно → В архиве, На модерации → В архиве, '
    'В архиве → На модерации.',
)
class ChangeStatusUpdateAPIView(generics.UpdateAPIView):
    """Endpoint for change status in realty"""

    queryset = realty_models.Realty.objects.all()
    serializer_class = common_serializers.RealtyStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save()


@extend_schema(
    tags=['Недвижимость | Основные'],
    summary='Получение данных для фильтров',
    description='Возвращает все возможные значения для фильтров: типы недвижимости, '
    'статусы, метро, районы и т.д.',
)
class RealtyFilterOptionsView(views.APIView):
    """
    API для получения всех возможных значений фильтров.
    """

    def get(self, request, *args, **kwargs):
        # Получаем данные
        data = {
            'realty_type': [
                {'id': rt.id, 'type': rt.type}
                for rt in realty_values_models.RealtyType.objects.all()
            ],
            'address': {
                'street': {
                    'zone': [
                        {'id': bt.id, 'name': bt.name}
                        for bt in realty_addresses_models.Zone.objects.all()
                    ],
                    'district': [
                        {'id': bt.id, 'name': bt.name}
                        for bt in realty_addresses_models.District.objects.all()
                    ],
                    'city': [
                        {'id': bt.id, 'name': bt.name}
                        for bt in realty_addresses_models.City.objects.all()
                    ],
                },
                'metro': [
                    {
                        'id': bt.id,
                        'name': bt.name,
                        'name_full': bt.name_full,
                        'color': bt.line.color,
                    }
                    for bt in realty_addresses_models.Metro.objects.all()
                ],
            },
            'about_building': {
                'type': [
                    {'id': bt.id, 'type': bt.type}
                    for bt in realty_values_models.BuildingType.objects.all()
                ]
            },
            'about_apartment': {
                'rooms_number': [
                    {
                        'id': apt.id,
                        'number_of_rooms': apt.number_of_rooms,
                    }
                    for apt in realty_values_models.RoomsNumber.objects.all()
                ]
            },
            'common_characteristics': {
                'repair_types': [
                    {'id': rt.id, 'type': rt.type}
                    for rt in realty_values_models.RepairType.objects.all()
                ],
                'bathroom_types': [
                    {'id': bt.id, 'type': bt.type}
                    for bt in realty_values_models.BathroomType.objects.all()
                ],
            },
            'owner_type': {
                'trade_participant': [
                    {
                        'id': apt.id,
                        'participant': apt.participant,
                    }
                    for apt in realty_values_models.TradeParticipant.objects.all()
                ]
            },
            'communication_method': [
                {
                    'id': apt.id,
                    'method': apt.method,
                }
                for apt in realty_values_models.CommunicationMethod.objects.all()
            ],
            'realty_status': {
                'realty_adv_status': [
                    {
                        'id': apt.id,
                        'status': apt.status,
                    }
                    for apt in realty_values_models.RealtyAdvStatus.objects.all()
                ]
            },
            'sales_parameters': {
                'housing_type': [
                    {'id': apt.id, 'type': apt.type}
                    for apt in realty_values_models.HousingType.objects.all()
                ],
                'sale_type': [
                    {'id': apt.id, 'type': apt.type}
                    for apt in realty_values_models.SaleType.objects.all()
                ],
            },
            'rent': {
                'lease_payments': {
                    'counters_payment': {
                        'trade_participant': [
                            {
                                'id': apt.id,
                                'participant': apt.participant,
                            }
                            for apt in realty_values_models.TradeParticipant.objects.all()
                        ]
                    },
                    'communal_payment': {
                        'trade_participant': [
                            {
                                'id': apt.id,
                                'participant': apt.participant,
                            }
                            for apt in realty_values_models.TradeParticipant.objects.all()
                        ]
                    },
                }
            },
        }
        return Response(data)


@extend_schema(
    tags=['Недвижимость | Управление'],
    summary='Удаление объявления (soft delete)',
    description='Мягкое удаление объявления. Объявление становится недоступным для просмотра, '
    'но остаётся в базе данных. Доступно только владельцу объявления.',
)
class RealtyDeleteView(generics.DestroyAPIView):
    queryset = realty_models.Realty.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {'detail': 'У вас нет прав на удаление этого объявления.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            instance.is_deleted
        ):  # <-- YYY --- Проверка на то, что объявление уже удалено
            return Response(
                {'detail': 'Объявление уже удалено.'},
                status=status.HTTP_400_BAD_REQUEST,  # <-- YYY --- realty_удаление v1
            )

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Недвижимость | Основные'],
    summary='Получение нескольких объявлений по списку ID',
    description='Возвращает массив объявлений в том же порядке, что и запрошенные ID. '
    'Оптимизация для функции сравнения.',
    parameters=[
        OpenApiParameter(
            name='ids',
            description='Список ID через запятую (например, ids=1,2,3). '
            f'Не больше {constants.BATCH_IDS_MAX} штук за запрос.',
            required=True,
            type=str,
        ),
    ],
    responses={200: realty_serializers.RealtyBaseSerializer(many=True)},
)
class RealtyBatchView(GenericAPIView):
    """
    Получение нескольких объявлений по списку ID.
    GET /realty/batch/?ids=1,2,3
    Возвращает массив объектов в том же порядке, что и запрошенные ID.
    """

    serializer_class = RealtyBaseSerializer
    queryset = Realty.objects.all()

    def get(self, request):
        # Получаем параметр ids из запроса
        ids_param = request.query_params.get('ids')

        if not ids_param:
            return Response(
                {'error': 'Parameter "ids" is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
            # Разбираем строку "1,2,3" в список чисел
        try:
            parsed_ids = [int(item.strip()) for item in ids_param.split(',')]
        except ValueError:
            return Response(
                {'error': 'Invalid ID format. Use comma-separated numbers'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        id_list = list(dict.fromkeys(parsed_ids))

        if len(id_list) > constants.BATCH_IDS_MAX:
            return Response(
                {'error': f'Too many ids, {constants.BATCH_IDS_MAX} max'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        realties = Realty.objects.filter(
            id__in=id_list,
            is_deleted=False,
            owner__is_deleted=False,
        )

        # Сохраняем порядок как в запросе
        # Создаём словарь {id: объект} для быстрого доступа
        realty_dict = {realty.id: realty for realty in realties}

        # Формируем результат в том же порядке, что и запрошенные ID
        result = [
            realty_dict[realty_id] for realty_id in id_list if realty_id in realty_dict
        ]

        # Сериалезуем
        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data)


# ========== КАТАЛОГИ НЕДВИЖИМОСТИ (4 типа) ==========
class BaseCatalogView(generics.ListAPIView):
    """Базовый класс для каталогов с предустановленными фильтрами."""

    permission_classes = [AllowAny]
    serializer_class = RealtyBaseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CatalogPriceFilter
    ordering_fields = ['price', 'published_at']
    ordering = ['-published_at']  # сначала новые

    def get_queryset(self):
        return Realty.objects.filter(
            is_deleted=False,
            realty_status=1,  # Активно
            **self.get_extra_filters(),
        )

    def get_extra_filters(self):
        """Метод для переопределения фильтров в дочерних классах."""
        return {}


@extend_schema(
    tags=['Недвижимость | Каталоги'],
    summary='Каталог: продажа жилой недвижимости',
    description='Возвращает список квартир, домов и другой жилой недвижимости на продажу',
    parameters=[
        OpenApiParameter(
            name='price_min', description='Мин. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='price_max', description='Макс. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='ordering',
            description='Сортировка (price, -price, published_at)',
            required=False,
            type=str,
        ),
    ],
)
class CatalogSaleResidentialView(BaseCatalogView):
    """Каталог: продажа жилой недвижимости"""

    def get_extra_filters(self):
        return {
            'sale_profile__isnull': False,  # есть продажа
            'realty_type__is_commercial': False,  # жилая
        }


@extend_schema(
    tags=['Недвижимость | Каталоги'],
    summary='Каталог: продажа коммерческой недвижимости',
    description='Возвращает список коммерческой недвижимости на продажу (офисы, склады, помещения)',
    parameters=[
        OpenApiParameter(
            name='price_min', description='Мин. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='price_max', description='Макс. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='ordering',
            description='Сортировка (price, -price, published_at)',
            required=False,
            type=str,
        ),
    ],
)
class CatalogSaleCommercialView(BaseCatalogView):
    """Каталог: продажа коммерческой недвижимости"""

    def get_extra_filters(self):
        return {
            'sale_profile__isnull': False,  # есть продажа
            'realty_type__is_commercial': True,  # коммерческая
        }


@extend_schema(
    tags=['Недвижимость | Каталоги'],
    summary='Каталог: аренда жилой недвижимости',
    description='Возвращает список квартир, домов и другой жилой недвижимости в аренду',
    parameters=[
        OpenApiParameter(
            name='price_min', description='Мин. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='price_max', description='Макс. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='ordering',
            description='Сортировка (price, -price, published_at)',
            required=False,
            type=str,
        ),
    ],
)
class CatalogRentResidentialView(BaseCatalogView):
    """Каталог: аренда жилой недвижимости"""

    def get_extra_filters(self):
        return {
            'rent_profile__isnull': False,  # есть аренда
            'realty_type__is_commercial': False,  # жилая
        }


@extend_schema(
    tags=['Недвижимость | Каталоги'],
    summary='Каталог: аренда коммерческой недвижимости',
    description='Возвращает список коммерческой недвижимости в аренду (офисы, склады, помещения)',
    parameters=[
        OpenApiParameter(
            name='price_min', description='Мин. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='price_max', description='Макс. цена', required=False, type=int
        ),
        OpenApiParameter(
            name='ordering',
            description='Сортировка (price, -price, published_at)',
            required=False,
            type=str,
        ),
    ],
)
class CatalogRentCommercialView(BaseCatalogView):
    """Каталог: аренда коммерческой недвижимости"""

    def get_extra_filters(self):
        return {
            'rent_profile__isnull': False,  # есть аренда
            'realty_type__is_commercial': True,  # коммерческая
        }
