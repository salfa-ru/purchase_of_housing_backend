from django.db.models import Q
from rest_framework import generics, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .models import Sale, Rent, Realty
from .pagination import LimitRealtyPagination, LimitShortRealtyPagination
from .serializers import (ShortSaleSerializer, ShortRentSerializer,
                          ShortRealtySerializer,
                          RealtyBaseSerializer)  # RealtySerializer
from .filters import RealtyFilter


# class LastSalesView(generics.ListAPIView):
#     queryset = Sale.objects.all().order_by("-realty__published_at")[:3]
#     serializer_class = ShortSaleSerializer


# class LastRentsView(generics.ListAPIView):
#     queryset = Rent.objects.all().order_by("-realty__published_at")[:3]
#     serializer_class = ShortRentSerializer


class LastRealtyListView(generics.ListAPIView):
    serializer_class = ShortRealtySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RealtyFilter
    pagination_class = LimitShortRealtyPagination

    def get_queryset(self):
        queryset = Realty.objects.filter(
            Q(sale_profile__isnull=False) | Q(rent_profile__isnull=False)
        ).order_by('-published_at')
        queryset = self.filter_queryset(queryset)
        return queryset


class RealtyListView(viewsets.ReadOnlyModelViewSet):
    queryset = Realty.objects.all().order_by('-published_at')
    serializer_class = RealtyBaseSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitRealtyPagination
    filterset_class = RealtyFilter
