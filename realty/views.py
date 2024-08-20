from rest_framework import viewsets

from .models import Realty, Sale, Rent
from .serializers import RealtySerializer, SaleSerializer, RentSerializer


# class LatestRealtyViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Realty.objects.order_by("-published_at")[:3]
#     serializer_class = RealtySerializer


class LastSalesView(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = SaleSerializer


class LastRentsView(viewsets.ReadOnlyModelViewSet):
    queryset = Rent.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = RentSerializer
