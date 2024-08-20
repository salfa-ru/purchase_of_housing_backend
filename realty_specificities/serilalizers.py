from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from realty_specificities import models as spec_models
from realty_values import serializers as values_serializers


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


class RentalFeaturesSerilalizer(serializers.ModelSerializer):
    """Rental Feature serializer."""

    class Meta:
        model = spec_models.RentalFeatures
        fields = "__all__"


class LeasePaymentsSerializer(serializers.ModelSerializer):
    """Lease Payments Serializer."""

    counters_payment = values_serializers.TradeParticipantSerializer()
    communal_payment = values_serializers.TradeParticipantSerializer()

    class Meta:
        model = spec_models.LeasePayments
        fields = "__all__"


class SalesParametersSerializer(serializers.ModelSerializer):
    """Sales Parameters Serializer."""

    housing_type = values_serializers.HousingTypeSerializer()
    sale_type = values_serializers.SaleTypeSerializer()

    class Meta:
        model = spec_models.SalesParameters
        fields = "__all__"
