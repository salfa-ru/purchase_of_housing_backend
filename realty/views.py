from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend

from .models import Sale, Rent, Realty
from .serializers import (ShortSaleSerializer, ShortRentSerializer,
                          RealtySerializer)
from .filters import RealtyFilter


class LastSalesView(generics.ListAPIView):
    queryset = Sale.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = ShortSaleSerializer


class LastRentsView(generics.ListAPIView):
    queryset = Rent.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = ShortRentSerializer


class RealtyListView(generics.ListAPIView):
    queryset = Realty.objects.all().order_by('-published_at')
    serializer_class = RealtySerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    filterset_class = RealtyFilter
