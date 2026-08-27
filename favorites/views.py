from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from .serializers import FavoriteSerializer

REALTY_TYPE_MAP = {
    'apartment': 'Квартира',
    'apartments': 'Квартира',
    'flat': 'Квартира',
    'house': 'Дом',
}

COMMERCIAL_ALIAS = 'commercial'


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


@extend_schema(
    tags=['Избранные'],
    summary='Получение списка избранного пользователя',
    description='Возвращает страницу объявлений в избранном с количеством непросмотренных. Поддерживает фильтрацию по trade_type, is_commercial и ordering.',
    parameters=[
        OpenApiParameter(
            name='page',
            description=f'Номер страницы (по {constants.FAVORITES_PAGESIZE_DEFAULT} объявления на странице)',
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name='trade_type', description='sale или rent', required=False, type=str
        ),
        OpenApiParameter(
            name='is_commercial',
            description='true — коммерческая, false — жилая',
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
            description='-added_at (сначала новые)',
            required=False,
            type=str,
        ),
    ],
)
class FavoriteListView(generics.ListAPIView):
    """
    Возвращает список избранных объявлений текущего пользователя.

    Поддерживает фильтрацию:
    - `trade_type` — тип сделки (sale/rent)
    - `is_commercial` — тип недвижимости (true — коммерческая, false — жилая)
    - `realty_type` — тип недвижимости. Принимает как русские названия
      (Квартира, Апартаменты, Дом и т.д.), так и английские алиасы
      (apartment, apartments, flat, house, commercial). Регистр не важен.
      Несколько типов перечисляются через запятую: `Квартира,Апартаменты`.
      Неизвестный тип — 400 со списком допустимых значений.
    - `ordering` — сортировка по дате добавления (added_at / -added_at)

    Выдача постраничная, страница выбирается параметром `page`.

    Ответ содержит:
    - `unviewed_count` — количество новых объявлений, добавленных после последнего посещения
      (считается по всему избранному, а не по текущей странице)
    - `count`, `page_size`, `pages_total`, `current_page`, `next`, `previous` — навигация по страницам
    - `results` — объекты избранного текущей страницы с полными данными объявлений

    Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    pagination_class = FavoritePagination

    def get_queryset(self):
        user = self.request.user
        queryset = Favorite.objects.filter(user=user)

        # Фильтрация по типу сделки (sale/rent)
        trade_type = self.request.query_params.get('trade_type')
        if trade_type:
            if trade_type.lower() == 'sale':
                queryset = queryset.filter(realty__sale_profile__isnull=False)
            elif trade_type.lower() == 'rent':
                queryset = queryset.filter(realty__rent_profile__isnull=False)

        # Фильтрация по типу недвижимости (жилая/коммерческая)
        is_commercial = self.request.query_params.get('is_commercial')
        if is_commercial is not None:
            if is_commercial.lower() == 'true':
                queryset = queryset.filter(realty__realty_type__is_commercial=True)
            elif is_commercial.lower() == 'false':
                queryset = queryset.filter(realty__realty_type__is_commercial=False)

        # Фильтрация по типу недвижимости (Квартира, Апартаменты, Дом и т.д.)
        realty_type = self.request.query_params.get('realty_type')
        if realty_type is not None:
            queryset = queryset.filter(
                realty__realty_type__type__in=resolve_realty_types(realty_type)
            )

        # Сортировка
        ordering = self.request.query_params.get('ordering', 'added_at')
        return queryset.order_by(ordering)

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


@extend_schema(
    tags=['Избранные'],
    summary='Добавление объявления в избранное',
    description='Принимает realty_id и добавляет объявление в избранное текущего пользователя',
    request=FavoriteSerializer,
    responses={201: FavoriteSerializer},
)
class FavoriteCreateView(generics.CreateAPIView):
    """
    Добавляет объявление в избранное текущего пользователя.

    Ожидает JSON:
    {
        "realty_id": 123
    }

    Возвращает созданный объект избранного с вложенными данными объявления.

    Если объявление уже в избранном — возвращает ошибку 400.
    Доступно только авторизованным пользователям.
    """

    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
    responses={200: None},
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

    def post(self, request):
        # Обновляем все непросмотренные записи текущего пользователя
        updated = Favorite.objects.filter(user=request.user, is_viewed=False).update(
            is_viewed=True
        )

        return Response(
            {'status': 'viewed', 'update_count': updated},
            status=status.HTTP_204_NO_CONTENT,
        )
