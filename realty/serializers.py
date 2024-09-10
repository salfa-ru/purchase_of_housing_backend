from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from realty import models as realty_models
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty_addresses import serializers as address_serializers
from realty_specificities import serializers as specif_serializers
from config import constants


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Realty Base Read Serializer."""

    owner = SlugRelatedField(slug_field="username", read_only=True)
    realty_type = SlugRelatedField(
        slug_field="type", queryset=values_models.RealtyType.objects.all()
    )
    address = address_serializers.AddressReadSerializer()
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
    """Realty Create Serializer."""

    owner = SlugRelatedField(slug_field="email", read_only=True)
    realty_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RealtyType.objects.all(),
        required=True,
    )
    description = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    address = address_serializers.AddressCreateSerializer(
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

    class Meta:
        model = realty_models.Realty
        fields = [
            "id",
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
        ]

    def create(self, validated_data):
        return self._create_realty(validated_data)

    def _create_realty(self, validated_data):
        address_data = validated_data.pop("address", None)
        about_building_data = validated_data.pop("about_building", None)
        about_apartment_data = validated_data.pop("about_apartment", None)
        common_characteristics_data = validated_data.pop(
            "common_characteristics", None
        )

        if address_data:
            address_serializer = address_serializers.AddressCreateSerializer(
                data=address_data
            )
            address_serializer.is_valid(raise_exception=True)
            address = address_serializer.save()
            validated_data["address"] = address

        if about_building_data:
            about_building, _ = (
                specificities_models.AboutBuilding.objects.get_or_create(
                    **about_building_data
                )
            )
            validated_data["about_building"] = about_building

        if about_apartment_data:
            about_apartment, _ = (
                specificities_models.AboutApartment.objects.get_or_create(
                    **about_apartment_data
                )
            )
            validated_data["about_apartment"] = about_apartment

        if common_characteristics_data:
            common_characteristics, _ = (
                specificities_models.CommonCharacteristics.objects.get_or_create(
                    **common_characteristics_data
                )
            )
            validated_data["common_characteristics"] = common_characteristics

        if "realty_status" not in validated_data:
            default_status, _ = (
                values_models.RealtyAdvStatus.objects.get_or_create(
                    status=constants.REALTY_STATUS
                )
            )
            validated_data["realty_status"] = default_status

        realty = realty_models.Realty.objects.create(**validated_data)
        return realty


class RentCreateSerializer(serializers.ModelSerializer):
    """Rent Create Serializer."""

    realty = RealtyCreateSerializer(required=True)
    rental_features = specif_serializers.RentalFeaturesSerilalizer(
        required=False
    )
    lease_payments = specif_serializers.LeasePaymentsCreateSerializer(
        required=False
    )

    def create(self, validated_data):
        realty_data = validated_data.pop("realty", None)
        rental_features_data = validated_data.pop("rental_features", None)
        lease_payments_data = validated_data.pop("lease_payments", None)

        if realty_data:
            realty_data["owner"] = self.context["request"].user
            realty = RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data["realty"] = realty

        if rental_features_data:
            rental_features = (
                specificities_models.RentalFeatures.objects.create(
                    **rental_features_data
                )
            )
            validated_data["rental_features"] = rental_features

        if lease_payments_data:
            lease_payments = specificities_models.LeasePayments.objects.create(
                **lease_payments_data
            )
            validated_data["lease_payments"] = lease_payments
        validated_data.pop("owner", None)
        rent = realty_models.Rent.objects.create(**validated_data)
        return rent

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class SaleCreateSerializer(serializers.ModelSerializer):
    """Sale Create Serializer."""

    realty = RealtyCreateSerializer(required=True)

    class Meta:
        model = realty_models.Sale
        exclude = [
            "sales_parameters",
        ]

    def create(self, validated_data):
        realty_data = validated_data.pop("realty", None)

        if realty_data:
            realty_data["owner"] = self.context["request"].user
            realty = RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data["realty"] = realty

        if "sales_parameters" not in validated_data:
            housing_type, _ = values_models.HousingType.objects.get_or_create(
                type=constants.HOUSING_TYPE
            )
            sale_type, _ = values_models.SaleType.objects.get_or_create(
                type=constants.SALE_TYPE
            )
            sales_parameters, _ = (
                specificities_models.SalesParameters.objects.get_or_create(
                    housing_type=housing_type, sale_type=sale_type
                )
            )
            validated_data["sales_parameters"] = sales_parameters

        validated_data.pop("owner", None)
        sale = realty_models.Sale.objects.create(**validated_data)
        return sale
