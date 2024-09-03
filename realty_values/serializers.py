from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from realty_values import models as values_models


class BuildingTypeSerializer(serializers.ModelSerializer):
    """Building Type serilalizer."""

    class Meta:
        model = values_models.BuildingType
        fields = "__all__"


class RoomsNumberSerializer(serializers.ModelSerializer):
    """Number of Romms Serilalizer."""

    class Meta:
        model = values_models.RoomsNumber
        fields = "__all__"


class RepairTypeSerilalizer(serializers.ModelSerializer):
    """Repair Type Serializer."""

    class Meta:
        model = values_models.RepairType
        fields = "__all__"


class BathroomTypeSerializer(serializers.ModelSerializer):
    """Bathroom Type Serializer."""

    class Meta:
        model = values_models.BathroomType
        fields = "__all__"
