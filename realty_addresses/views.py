from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config import constants
from realty.filters import RealtyFilter
from realty.models import Realty
from realty.serializers.serializers_realty import ShortRealtySerializer
from realty_addresses.serializers import (
    MapPointsSerializer, MapPointsRequestSerializer,
    GetAnnouncementsInMapPointRequestSerializer)
from realty_values import models as models_values


@extend_schema(
    summary='Получение списка точек на карте с объявлениями',
    description=(
            'Возвращает список точек с объявлениями в пределах заданного прямоугольника. '
            'Необходимо указать координаты верхнего левого и нижнего правого углов, '
            'а также (опционально) параметры для фильтрации.'
    ),
    request=MapPointsRequestSerializer,
    responses=MapPointsSerializer(many=True),
)
class GetlistMapPointsAPIView(APIView):
    """ Get list realty's point in map"""
    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    ).order_by('-published_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        serializer = MapPointsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        top_left_latitude = request.data.get('top_left_latitude')
        top_left_longitude = request.data.get('top_left_longitude')
        bottom_right_latitude = request.data.get('bottom_right_latitude')
        bottom_right_longitude = request.data.get('bottom_right_longitude')

        # получаем ID статуса объявления со значением Активно
        realty_status = models_values.RealtyAdvStatus.objects.get(
            status="Активно").pk

        queryset = Realty.objects.filter(
            Q(address__latitude__gte=bottom_right_latitude) &
            Q(address__latitude__lte=top_left_latitude) &
            Q(address__longitude__gte=top_left_longitude) &
            Q(address__longitude__lte=bottom_right_longitude) &
            Q(realty_status=realty_status)
        )

        filterset = self.filterset_class(
            request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(
                filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs

        response_serializer = MapPointsSerializer(queryset, many=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
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
    """Get List realty in point"""
    queryset = Realty.objects.all().filter(
        realty_status__status=constants.ADVERTISMENT_STATUS
    ).order_by('-published_at')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        serializer = GetAnnouncementsInMapPointRequestSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)

        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response(
                {"error": "Пожалуйста, укажите все необходимые данные!"},
                status=status.HTTP_400_BAD_REQUEST)

        # получаем ID статуса объявления со значением Активно
        realty_status = models_values.RealtyAdvStatus.objects.get(
            status="Активно").pk

        queryset = Realty.objects.filter(
            Q(address__latitude=latitude) &
            Q(address__longitude=longitude) &
            Q(realty_status=realty_status)
        )

        filterset = self.filterset_class(
            request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(
                filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        serializer = ShortRealtySerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
