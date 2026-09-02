from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config import constants
from realty.models import Realty
from realty_values.models import RealtyType

from .models import Favorite
from .paginations import FavoritePagination
from .serializers import FavoriteSerializer, FavoriteViewedSerializer

REALTY_TYPE_MAP = {
    'apartment': 'Квартира',
    'apartments': 'Квартира',
    'flat': 'Квартира',
    'house': 'Дом',
}

COMMERCIAL_ALIAS = 'commercial'

TRADE_TYPES = ('sale', 'rent')
BOOLEAN_VALUES = {'true': True, 'false': False}
ORDERING_VALUES = ('added_at', '-added_at')


def invalid_value_error(param, raw, allowed):
    """Единый текст ошибки для параметров с закрытым списком значений."""
    return ValidationError(
        {
            param: f"Недопустимое значение '{raw}'. "
            f'Допустимые значения: {", ".join(allowed)}.'
        }
    )


def resolve_realty_types(raw):
    """
    Разбирает параметр realty_type: запятая разделяет несколько типов.
    Принимает русские названия из справочника и английские алиасы,
    регистр не важен. Возвращает список канонических названий типов
    для фильтрации.
    """
    catalog = list(RealtyType.objects.values_list('type', 'is_commercial'))
    known = {value.lower(): value for value, _ in catalog}
    commercial = [value for value, is_commercial in catalog if is_commercial]

    resolved = []
    unknown = []
    for part in (item.strip() for item in raw.split(',')):
        if not part:
            continue
        if part.lower() == COMMERCIAL_ALIAS:
            if not commercial:
                unknown.append(part)
                continue
            for value in commercial:
                if value not in resolved:
                    resolved.append(value)
            continue
        canonical = known.get(REALTY_TYPE_MAP.get(part.lower(), part).lower())
        if canonical is None:
            unknown.append(part)
        elif canonical not in resolved:
            resolved.append(canonical)

    if unknown or not resolved:
        allowed = ', '.join(sorted(known.values()))
        if unknown:
            listed = ', '.join(f"'{item}'" for item in unknown)
            message = f'Недопустимое значение {listed}.'
        else:
            message = 'Значение не может быть пустым.'
        raise ValidationError(
            {'realty_type': f'{message} Допустимые значения: {allowed}.'}
        )
    return resolved


def resolve_trade_type(raw):
    """sale или rent, регистр не важен. Иначе — 400."""
    value = raw.strip().lower()
    if value not in TRADE_TYPES:
        raise invalid_value_error('trade_type', raw, TRADE_TYPES)
    return value


def resolve_is_commercial(raw):
    """true или false, регистр не важен. Иначе — 400."""
    value = raw.strip().lower()
    if value not in BOOLEAN_VALUES:
        raise invalid_value_error('is_commercial', raw, BOOLEAN_VALUES)
    return BOOLEAN_VALUES[value]


def resolve_ordering(raw):
    """Сортировка только по дате добавления: поле уходит прямо в order_by,
    поэтому произвольное значение уронило бы запрос в 500."""
    value = raw.strip()
    if value not in ORDERING_VALUES:
        raise invalid_value_error('ordering', raw, ORDERING_VALUES)
    return value


FAVORITE_LIST_PARAMETERS = [
    OpenApiParameter(
        name='page',
        description=f'Номер страницы (по {constants.FAVORITES_PAGESIZE_DEFAULT} объявления на странице)',
        required=False,
        type=int,
    ),
    OpenApiParameter(
        name='trade_type',
        description='sale или rent. Другое значение — 400.',
        required=False,
        type=str,
        enum=TRADE_TYPES,
    ),
    OpenApiParameter(
        name='is_commercial',
        description='true — коммерческая, false — жилая. Другое значение — 400.',
        required=False,
        type=bool,
    ),
    OpenApiParameter(
        name='realty_type',
        description='Тип недвижимости: русское название из справочника '
        '(Квартира, Апартаменты) или английский алиас (apartment, flat). '
        'Регистр не важен. Несколько типов перечисляются через запятую: '
        'Квартира,Апартаменты. Неизвестный тип — 400.',
        required=False,
        type=str,
    ),
    OpenApiParameter(
        name='ordering',
        description='-added_at (сначала новые, по умолчанию) или added_at '
        '(сначала старые). Другое значение — 400.',
        required=False,
        type=str,
        enum=ORDERING_VALUES,
    ),
]

FAVORITE_LIST_SCHEMA = extend_schema(
    tags=['Избранные'],
    summary='Получение списка избранного пользователя',
    description='Возвращает страницу объявлений в избранном с количеством непросмотренных. Поддерживает фильтрацию по trade_type, is_commercial, realty_type и ordering.',
    parameters=FAVORITE_LIST_PARAMETERS,
)

FAVORITE_CREATE_SCHEMA = extend_schema(
    tags=['Избранные'],
    summary='Добавление объявления в избранное',
    description='Принимает realty_id и добавляет объявление в избранное текущего пользователя',
    request=FavoriteSerializer,
    responses={201: FavoriteSerializer},
)


@extend_schema_view(get=FAVORITE_LIST_SCHEMA, post=FAVORITE_CREATE_SCHEMA)
class FavoriteListCreateView(generics.ListCreateAPIView):
    """
    Список избранного текущего пользователя и добавление в него объявления.

    GET поддерживает фильтрацию:
    - `trade_type` — тип сделки (sale/rent)
    - `is_commercial` — тип недвижимости (true — коммерческая, false — жилая)
    - `realty_type` — тип недвижимости. Принимает как русские названия
      (Квартира, Апартаменты, Дом и т.д.), так и английские алиасы
      (apartment, apartments, flat, house, commercial). Регистр не важен.
      Несколько типов перечисляются через запятую: `Квартира,Апартаменты`.
    - `ordering` — сортировка по дате добавления (`-added_at` по умолчанию)

    Недопустимое значение любого из фильтров — 400 со списком допустимых.

    Выдача постраничная, страница выбирается параметром `page`.

    Ответ содержит:
    - `unviewed_count` — количество новых объявлений, добавленных после последнего посещения
      (считается по всему избранному, а не по текущей странице)
    - `count`, `page_size`, `pages_total`, `current_page`, `next`, `previous` — навигация по страницам
    - `results` — объекты избранного текущей страницы с полными данными объявлений

    POST ожидает JSON:
    {
        "realty_id": 123
    }

    и возвращает созданный объект избранного с вложенными данными объявления.
    Если объявление уже в избранном — 400.

    Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    pagination_class = FavoritePagination

    def get_queryset(self):
        user = self.request.user
        queryset = Favorite.objects.filter(user=user)
        params = self.request.query_params

        # Фильтрация по типу сделки (sale/rent)
        trade_type = params.get('trade_type')
        if trade_type is not None:
            if resolve_trade_type(trade_type) == 'sale':
                queryset = queryset.filter(realty__sale_profile__isnull=False)
            else:
                queryset = queryset.filter(realty__rent_profile__isnull=False)

        # Фильтрация по типу недвижимости (жилая/коммерческая)
        is_commercial = params.get('is_commercial')
        if is_commercial is not None:
            queryset = queryset.filter(
                realty__realty_type__is_commercial=resolve_is_commercial(is_commercial)
            )

        # Фильтрация по типу недвижимости (Квартира, Апартаменты, Дом и т.д.)
        realty_type = params.get('realty_type')
        if realty_type is not None:
            queryset = queryset.filter(
                realty__realty_type__type__in=resolve_realty_types(realty_type)
            )

        # Сортировка
        return queryset.order_by(resolve_ordering(params.get('ordering', '-added_at')))

    def list(self, request, *args, **kwargs):
        """
        Переопределяем, чтоб добавить unviewed_count в ответ.
        """

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        unviewed_count = queryset.filter(is_viewed=False).count()

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            paginated_response.data = {
                'unviewed_count': unviewed_count,
                **paginated_response.data,
            }
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        return Response({'unviewed_count': unviewed_count, 'results': serializer.data})

    def create(self, request, *args, **kwargs):
        """Переопределяем create для добавления проверок"""

        # 1. Проверяем, что realty_id передан
        realty_id = request.data.get('realty_id')
        if not realty_id:
            raise ValidationError({'realty_id': 'Это поле обязательно'})

        # 2. Проверяем, существует ли объявление
        try:
            realty = Realty.objects.get(id=realty_id)
        except Realty.DoesNotExist as err:
            raise NotFound({'detail': 'Объявление не найдено'}) from err

        # 3. Проверяем, не добавлено ли уже в избранное
        if Favorite.objects.filter(user=request.user, realty=realty).exists():
            raise ValidationError({'detail': 'Объявление уже добавлено в избранное'})

        # 4. Создаём объект избранного
        favorite = Favorite.objects.create(user=request.user, realty=realty)

        # 5. Сериализуем и возвращаем ответ
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        tags=['Избранные'],
        summary='Добавление объявления в избранное (устаревший адрес)',
        description='Оставлен ради обратной совместимости. '
        'Новый адрес — POST /api/favorites/.',
        request=FavoriteSerializer,
        responses={201: FavoriteSerializer},
        deprecated=True,
    )
)
class FavoriteCreateView(FavoriteListCreateView):
    """Устаревший алиас POST /api/favorites/create/."""

    http_method_names = ['post']


@extend_schema(
    tags=['Избранные'],
    summary='Удаление объявления из избранного',
    description='Мгновенное удаление без подтверждения. Возвращает 204 No Content.',
    responses={204: None},
)
class FavoriteDeleteView(generics.DestroyAPIView):
    """
    Удаляет объявление из избранного по ID записи избранного.

    Удаление происходит мгновенно, без дополнительного подтверждения.
    Пользователь может удалять только свои записи.

    Возвращает статус 204 No Content при успешном удалении.
    Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    queryset = Favorite.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        # Пользователь может удалять только свое избранное
        return self.queryset.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Избранные'],
    summary='Сброс счётчика непросмотренных',
    description='Помечает все объявления в избранном как просмотренные (is_viewed = True)',
    request=None,
    responses={200: FavoriteViewedSerializer},
)
class FavoriteMarkViewedView(APIView):
    """
    Сбрасывает счётчик новых объявлений в избранном.

    Вызывается при заходе пользователя на страницу /favorites.
    Устанавливает флаг `is_viewed = True` для всех непросмотренных записей текущего пользователя.

    Возвращает:
    {
        "status": "viewed",
        "update_count": количество обновлённых записей
    }

    Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteViewedSerializer

    def post(self, request):
        # Обновляем все непросмотренные записи текущего пользователя
        updated = Favorite.objects.filter(user=request.user, is_viewed=False).update(
            is_viewed=True
        )

        return Response(
            {'status': 'viewed', 'update_count': updated},
            status=status.HTTP_200_OK,
        )
