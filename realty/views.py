from rest_framework import generics

from .models import Sale, Rent
from .serializers import SaleSerializer, RentSerializer


class LastSalesView(generics.ListAPIView):
    queryset = Sale.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = SaleSerializer


class LastRentsView(generics.ListAPIView):
    queryset = Rent.objects.all().order_by("-realty__published_at")[:3]
    serializer_class = RentSerializer
