from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from django.core import validators

from realty_specificities import models as spec_models
from realty_values import models as values_models
from realty_values import serializers as values_serializers
from config import constants


class AboutBuildingSerializer(serializers.ModelSerializer):
    """About Building Serializer."""

    type = values_serializers.BuildingTypeSerializer()

    class Meta:
        model = spec_models.AboutBuilding
        fields = "__all__"


class AboutApartmentSerializer(serializers.ModelSerializer):
    """About Apartment Serializer."""

    number_of_rooms = values_serializers.RoomsNumberSerializer()

    class Meta:
        model = spec_models.AboutApartment
        fields = "__all__"


class CommonCharacteristicsSerializer(serializers.ModelSerializer):
    """Common Characteristics Serilalizer."""

    repair_type = values_serializers.RepairTypeSerilalizer()
    bathroom = values_serializers.BathroomTypeSerializer()

    class Meta:
        model = spec_models.CommonCharacteristics
        fields = "__all__"
