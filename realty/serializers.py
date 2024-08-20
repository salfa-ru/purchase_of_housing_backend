from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from realty import models as realty_models
from realty_values import models as values_models
from realty_specificities import models as specifities_models
from realty_addresses import serializers as address_serilizers
from realty_specificities import serilalizers as specif_serializers


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Realty Base Read Serializer."""

    owner = SlugRelatedField(slug_field="username", read_only=True)
    realty_type = SlugRelatedField(
        slug_field="type", queryset=values_models.RealtyType.objects.all()
    )
    address = address_serilizers.AddressSerializer()
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


class SaleCreateSerializer(serializers.ModelSerializer):
    """Realty Create Serializer."""

    owner = SlugRelatedField(slug_field="username", read_only=True)
    trade_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeType.objects.all()
    )
    realty_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RealtyType.objects.all()
    )

    class Meta:
        model = realty_models.Realty
        exclude = ["published_at", "changed_at"]

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        about_building_data = validated_data.pop("about_building")
        about_apartment_data = validated_data.pop("about_apartment")
        common_characteristics_data = validated_data.pop(
            "common_characteristics"
        )
        rental_features_data = validated_data.pop("rental_features")
        lease_payments_data = validated_data.pop("lease_payments")

        address = specifities_models.Address.objects.create(**address_data)
        about_building = specifities_models.AboutBuilding.objects.create(
            **about_building_data
        )
        about_apartment = specifities_models.AboutApartment.objects.create(
            **about_apartment_data
        )
        common_characteristics = (
            specifities_models.CommonCharacteristics.objects.create(
                **common_characteristics_data
            )
        )
        rental_features = specifities_models.RentalFeatures.objects.create(
            **rental_features_data
        )
        lease_payments = specifities_models.LeasePayments.objects.create(
            **lease_payments_data
        )

        realty = realty_models.Realty.objects.create(
            address=address,
            about_building=about_building,
            about_apartment=about_apartment,
            common_characteristics=common_characteristics,
            rental_features=rental_features,
            lease_payments=lease_payments,
            **validated_data
        )

        return realty


class RealtyUpdateSerializer(serializers.ModelSerializer):
    """Realty Update Serializer."""

    class Meta:
        model = realty_models.Realty
        ...


class RealtyReadSerializer(serializers.ModelSerializer):
    """Realty Read Serializer."""

    class Meta:
        model = realty_models.Realty
        ...


class RealtyDeleteSerializer(serializers.ModelSerializer):
    """Realty Delete Serializer."""

    class Meta:
        model = realty_models.Realty
        ...
