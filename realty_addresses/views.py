from rest_framework import viewsets

from realty_addresses import serializers as addresses_serializers
from realty_addresses import models as addresses_models


from users.models import User


class TestViewSet(viewsets.ModelViewSet):
    """Test viewset.
    Viewing, creating, editing, removal."""

    queryset = addresses_models.City.objects.all()
    # permission_classes =
    serializer_class = addresses_serializers.AddressCreateSerializer