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


class SalesParametersSerializer(serializers.ModelSerializer):
    """Serializer for SalesParameters."""

    housing_type = values_serializers.HousingTypeSerializer(read_only=True)
    sale_type = values_serializers.SaleTypeSerializer(read_only=True)

    class Meta:
        model = spec_models.SalesParameters
        fields = ['housing_type', 'sale_type']


class RentalFeaturesSerializer(serializers.ModelSerializer):
    """Serializer for RentalFeatures."""

    class Meta:
        model = spec_models.RentalFeatures
        fields = [
            'fridge', 'internet', 'conditioner', 'tv',
            'dishwasher', 'washing_machine', 'garbage_chute',
            'kids_allowed', 'animals_allowed'
        ]


class LeasePaymentsSerializer(serializers.ModelSerializer):
    """Serializer for LeasePayments."""

    counters_payment = values_serializers.TradeParticipantSerializer(read_only=True)
    communal_payment = values_serializers.TradeParticipantSerializer(read_only=True)

    class Meta:
        model = spec_models.LeasePayments
        fields = ['counters_payment', 'communal_payment', 'deposit']
