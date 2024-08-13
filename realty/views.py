from rest_framework import viewsets

from .models import Realty
from .serializers import RealtySerializer


class LatestRealtyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Realty.objects.order_by("-published_at")[:3]
    serializer_class = RealtySerializer
