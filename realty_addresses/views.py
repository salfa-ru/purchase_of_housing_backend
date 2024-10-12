from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status, filters, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from realty.filters import RealtyFilter
from realty.models import Realty
from realty.pagination import LimitRealtyPagination
from realty_addresses.serializers import MapPointsSerializer, GetAnnouncementsInMapPoint


@extend_schema(
    summary='Получение списка точек на карте в которых есть объявления '
            'с заданными параметрами, в заданном прямоугольнике, на вход нужно '
            'подать кардинаты верхнего левого угла и нижнего правого угла карты для вывода списка точек на карте '
            'а так же передать параметры для фильтрации (опционально)')
class GetlistMapPointsAPIView(APIView):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        top_left_latitude = request.data.get('top_left_latitude')
        top_left_longitude = request.data.get('top_left_longitude')
        bottom_right_latitude = request.data.get('bottom_right_latitude')
        bottom_right_longitude = request.data.get('bottom_right_longitude')

        if (top_left_latitude is None or top_left_longitude is None or bottom_right_latitude is None or
                bottom_right_longitude is None):
            return Response(
                {"error": "Пожалуйста, укажите все необходимые данные!"},
                status=status.HTTP_400_BAD_REQUEST)

        queryset = Realty.objects.filter(
            Q(address__latitude__gte=bottom_right_latitude) &
            Q(address__latitude__lte=top_left_latitude) &
            Q(address__longitude__gte=top_left_longitude) &
            Q(address__longitude__lte=bottom_right_longitude)
        )

        filterset = self.filterset_class(request.data, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        serializer = MapPointsSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GetListAnnouncementsInMapPoint(APIView):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response(
                {"error": "Пожалуйста, укажите все необходимые данные!"},
                status=status.HTTP_400_BAD_REQUEST)

        queryset = Realty.objects.filter(
            Q(address__latitude=latitude) &
            Q(address__longitude=longitude)
        )

        filterset = self.filterset_class(request.data, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs

        serializer = GetAnnouncementsInMapPoint(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# @extend_schema(
#     summary='Получение списка точек на карте в которых есть объявления '
#             'с заданными параметрами, в заданном прямоугольнике')
# class AddressMapPointsListAPIView(generics.ListAPIView):
#     """Get a list of Realties coordinates."""
#
#     serializer_class = MapPointsSerializer
#     # pagination_class = LimitRealtyPagination
#     filter_backends = (DjangoFilterBackend,)
#     filterset_class = RealtyFilter
#
#     def get_queryset(self, *args, **kwargs):
#         # Получаем параметры из запроса
#         try:
#             top_left_latitude = self.request.data['top_left_latitude']
#             top_left_longitude = self.request.data['top_left_longitude']
#             bottom_right_latitude = self.request.data['bottom_right_latitude']
#             bottom_right_longitude = self.request.data['bottom_right_longitude']
#         except KeyError:
#             return Realty.objects.none()
#
#         # Фильтруем адреса, которые попадают в заданный прямоугольник
#         queryset = Realty.objects.filter(
#             Q(address__latitude__gte=bottom_right_latitude) &
#             Q(address__latitude__lte=top_left_latitude) &
#             Q(address__longitude__gte=top_left_longitude) &
#             Q(address__longitude__lte=bottom_right_longitude)
#         )
#
#         filtered_realty_queryset = self.filterset_class(self.request.data, queryset=queryset).qs
#
#         return filtered_realty_queryset
#
#     def get(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#
#         if not queryset.exists():
#             return Response(
#                 {"error": "Пожалуйста, укажите все необходимые данные!"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         return self.list(request, *args, **kwargs)
