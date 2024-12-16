from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from realty_values import models as values_models
from realty_values.models import RealtyType


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


class TradeParticipantSerializer(serializers.ModelSerializer):
    """Trade Participant Serializer."""

    class Meta:
        model = values_models.TradeParticipant
        fields = "__all__"


class HousingTypeSerializer(serializers.ModelSerializer):
    """Housing Type Serializer."""

    class Meta:
        model = values_models.HousingType
        fields = "__all__"


class SaleTypeSerializer(serializers.ModelSerializer):
    """Sale Type Serializer."""

    class Meta:
        model = values_models.SaleType
        fields = "__all__"


class RealtyTypeSerializer(serializers.ModelSerializer):  # создал собственный сериализатор
    class Meta:
        model = values_models.RealtyType
        fields = ["id", "type"]


class OwnerTypeSerializer(serializers.ModelSerializer):  # создал собственный сериализатор
    class Meta:
        model = values_models.TradeParticipant
        fields = ["id", "participant"]


class CommunicationMethodSerializer(serializers.ModelSerializer):  # создал собственный сериализатор
    class Meta:
        model = values_models.CommunicationMethod
        fields = ["id", "method"]
