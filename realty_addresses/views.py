from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters, generics
from rest_framework.response import Response
from realty.filters import RealtyFilter
from realty.models import Realty
from realty.pagination import LimitRealtyPagination
from realty_addresses.models import Address
from realty_addresses.serializers import AddressReadSerializer


class AddressMapPointsListAPIView(generics.ListAPIView):
    serializer_class = AddressReadSerializer
    pagination_class = LimitRealtyPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter

    def get_queryset(self):
        # Получаем параметры из запроса
        top_left_latitude = self.request.data.get('top_left_latitude')
        top_left_longitude = self.request.data.get('top_left_longitude')
        bottom_right_latitude = self.request.data.get('bottom_right_latitude')
        bottom_right_longitude = self.request.data.get('bottom_right_longitude')

        # Если параметры не переданы, возвращаем пустой QuerySet
        if not (top_left_latitude and top_left_longitude and bottom_right_latitude and bottom_right_longitude):
            return Address.objects.none()

        # Преобразуем координаты в числа с плавающей точкой
        try:
            top_left_latitude = float(top_left_latitude)
            top_left_longitude = float(top_left_longitude)
            bottom_right_latitude = float(bottom_right_latitude)
            bottom_right_longitude = float(bottom_right_longitude)
        except ValueError:
            return Address.objects.none()

        # Фильтруем адреса, которые попадают в заданный прямоугольник
        address_queryset = Address.objects.filter(
            Q(latitude__gte=bottom_right_latitude) &
            Q(latitude__lte=top_left_latitude) &
            Q(longitude__gte=top_left_longitude) &
            Q(longitude__lte=bottom_right_longitude)
        )

        # Применяем фильтры из RealtyFilter к модели Realty
        realty_queryset = Realty.objects.filter(address__in=address_queryset)

        # Применяем фильтры, если они указаны в запросе
        filtered_realty_queryset = self.filterset_class(self.request.data, queryset=realty_queryset).qs

        return filtered_realty_queryset


def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response({"error": "No addresses found within the specified coordinates."},
                            status=status.HTTP_404_NOT_FOUND)

        return self.list(request, *args, **kwargs)
