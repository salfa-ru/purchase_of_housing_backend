from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from config import constants
from realty.filters import RealtyFilter
from realty.models import Realty
from realty.serializers.serializers_realty import ShortRealtySerializer
from realty_addresses.filters import MetroFilter
from realty_addresses.serializers import (
    GetAnnouncementsInMapPointRequestSerializer,
    MapPointsRequestSerializer,
    MapPointsSerializer,
    MetroSerializer,
)

from .models import Metro


@extend_schema(
    tags=['Адреса и карты'],
    summary='Получение списка точек на карте с объявлениями',
    description=(
        'Возвращает точки опубликованных объявлений в видимой части карты: '
        'в теле запроса — координаты верхнего левого и нижнего правого углов. '
        'Пагинации нет, отдаются все точки.\n\n'
        'В query-параметрах принимаются те же фильтры, что и у списка '
        'объявлений (/api/realty/): цена, тип и т.д. Выделенная пользователем '
        'область передаётся так же, как в списке, — параметрами lat_min, '
        'lat_max, lon_min, lon_max. Тогда на карте остаются только точки '
        'внутри области, а видимую часть карты можно двигать как угодно.'
    ),
    request=MapPointsRequestSerializer,
    responses=MapPointsSerializer(many=True),
)
class GetlistMapPointsAPIView(APIView):
    """Точки объявлений на карте."""

    queryset = (
        Realty.objects.all()
        .filter(realty_status__status=constants.ADVERTISMENT_STATUS)
        .order_by('-published_at')
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        serializer = MapPointsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        corners = serializer.validated_data

        queryset = Realty.objects.filter(
            realty_status__status=constants.ADVERTISMENT_STATUS,
            address__latitude__gte=corners['bottom_right_latitude'],
            address__latitude__lte=corners['top_left_latitude'],
            address__longitude__gte=corners['top_left_longitude'],
            address__longitude__lte=corners['bottom_right_longitude'],
        ).select_related('address')

        filterset = self.filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs

        response_serializer = MapPointsSerializer(queryset, many=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Адреса и карты'],
    summary='Получение списка объявлений по заданной точке на карте ',
    description=(
        'Возвращает список объявлений в точке на карте. '
        'Необходимо указать координаты широты и долготы, '
        'а также (опционально) параметры для фильтрации.'
    ),
    request=GetAnnouncementsInMapPointRequestSerializer,
    responses=ShortRealtySerializer(many=True),
)
class GetListAnnouncementsInMapPoint(APIView):
    """Объявления в точке на карте."""

    queryset = (
        Realty.objects.all()
        .filter(realty_status__status=constants.ADVERTISMENT_STATUS)
        .order_by('-published_at')
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        serializer = GetAnnouncementsInMapPointRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        queryset = Realty.objects.filter(
            realty_status__status=constants.ADVERTISMENT_STATUS,
            address__latitude=serializer.validated_data['latitude'],
            address__longitude=serializer.validated_data['longitude'],
        )

        filterset = self.filterset_class(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        serializer = ShortRealtySerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Адреса и карты'],
    summary='Получение списка станций метро',
    description=(
        'Возвращает список станций метро с информацией о линиях. '
        'Поддерживает фильтрацию по названию станции и линии метро. '
        'Поиск осуществляется по частичному совпадению и не чувствителен к регистру. '
        'Возвращает 404, если станции не найдены.'
    ),
    responses={200: MetroSerializer(many=True), 404: None},
)
class MetroStationsAPIView(generics.ListAPIView):
    """Станции метро с необязательной фильтрацией."""

    serializer_class = MetroSerializer
    queryset = Metro.objects.select_related('line').all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = MetroFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not queryset.exists():
            return Response(
                {'detail': 'Станции метро не найдены.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
