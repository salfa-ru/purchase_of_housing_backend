from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from yaml import add_representer

from realty import models as realty_models
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty_addresses import serializers as address_serilizers
from realty_specificities import serilalizers as specif_serializers
from users import models as user_models
from config import constants
from realty_addresses import models as addresses_models
from realty import models as realty_models


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Realty Base Read Serializer."""

    owner = SlugRelatedField(slug_field="username", read_only=True)
    realty_type = SlugRelatedField(
        slug_field="type", queryset=values_models.RealtyType.objects.all()
    )
    address = address_serilizers.AddressReadSerializer()
    about_building = specif_serializers.AboutBuildingSerializer()
    about_apartment = specif_serializers.AboutApartmentSerializer()
    common_characteristics = (
        specif_serializers.CommonCharacteristicsSerializer()
    )
    owner_type = SlugRelatedField(
        slug_field="participant",
        queryset=values_models.TradeParticipant.objects.all(),
    )
    communication_method = SlugRelatedField(
        slug_field="method",
        queryset=values_models.CommunicationMethod.objects.all(),
    )
    realty_status = SlugRelatedField(
        slug_field="status",
        queryset=values_models.RealtyAdvStatus.objects.all(),
    )

    class Meta:
        model = realty_models.Realty
        # exclude = ["published_at", "changed_at"]
        fields = "__all__"


class SaleReadSerializer(serializers.ModelSerializer):
    """Sale Read Serializer."""

    realty = RealtyBaseSerializer()
    sales_parameters = specif_serializers.SalesParametersSerializer()

    class Meta:
        model = realty_models.Sale
        fields = "__all__"


class RentReadSerializer(serializers.ModelSerializer):
    """Rent Read Serializer."""

    realty = RealtyBaseSerializer()
    rental_features = specif_serializers.RentalFeaturesSerilalizer()
    lease_payments = specif_serializers.LeasePaymentsSerializer()

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class RealtyCreateSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=user_models.User.objects.all(),
        required=True,
    )
    realty_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RealtyType.objects.all(),
        required=True,
    )
    description = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    address = address_serilizers.AddressCreateSerializer(
        required=True,
    )
    about_building = specif_serializers.AboutBuildingCreateSerializer(
        required=False
    )
    about_apartment = specif_serializers.AboutApartmentCreateSerializer(
        required=False
    )
    common_characteristics = (
        specif_serializers.CommonCharacteristicsCreateSerializer(
            required=False
        )
    )
    price = serializers.IntegerField(
        required=True,
    )
    commission = serializers.IntegerField(
        required=False,
    )
    owner_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeParticipant.objects.all(),
        required=True,
    )
    communication_method = serializers.PrimaryKeyRelatedField(
        queryset=values_models.CommunicationMethod.objects.all(),
        required=True,
    )
    realty_status = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RealtyAdvStatus.objects.all(),
        required=True,
    )

    class Meta:
        model = realty_models.Realty
        fields = [
            "owner",
            "realty_type",
            "address",
            "about_building",
            "about_apartment",
            "common_characteristics",
            "description",
            "price",
            "commission",
            "owner_type",
            "communication_method",
            "realty_status",
        ]

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        about_building_data = validated_data.pop("about_building", None)
        about_apartment_data = validated_data.pop("about_apartment", None)
        common_characteristics_data = validated_data.pop(
            "common_characteristics", None
        )
        if address_data:
            address_serilizer = address_serilizers.AddressCreateSerializer(
                data=address_data
            )
            address_serilizer.is_valid(raise_exception=True)
            address = address_serilizer.save()
            validated_data["address"] = address
        if about_building_data:
            about_building = specificities_models.AboutBuilding.objects.create(
                **about_building_data
            )
            validated_data["about_building"] = about_building

        if about_apartment_data:
            about_apartment = (
                specificities_models.AboutApartment.objects.create(
                    **about_apartment_data
                )
            )
            validated_data["about_apartment"] = about_apartment

        if common_characteristics_data:
            common_characteristics = (
                specificities_models.CommonCharacteristics.objects.create(
                    **common_characteristics_data
                )
            )
            validated_data["common_characteristics"] = common_characteristics

        realty = realty_models.Realty.objects.create(**validated_data)
        return realty


# class RentCreateSerializer(serializers.ModelSerializer):
#     """Rent Create Serializer."""

#     realty = RealtyCreateSerializer()

