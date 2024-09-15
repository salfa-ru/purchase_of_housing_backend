from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from .models import Realty, Sale, Rent
from realty_photos.serializers import RealtyPhotoSerializer
from realty import models as realty_models
from realty_values import models as values_models
from realty_addresses import serializers as address_serializers
from realty_specificities import serializers as specif_serializers


class ShortRealtySerializer(serializers.ModelSerializer):
    """Realty Short Detail Read Serializer."""

    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    number_of_rooms = serializers.CharField(
        source="about_apartment.number_of_rooms.number_of_rooms"
    )
    realty_type = serializers.ReadOnlyField(source='realty_type.type')
    area = serializers.DecimalField(
        source="about_apartment.area",
        max_digits=10, decimal_places=2
    )
    street = serializers.ReadOnlyField(source='address.street.name')
    house_number = serializers.ReadOnlyField(source='address.house_number')
    corpus = serializers.ReadOnlyField(source='address.corpus')
    building = serializers.ReadOnlyField(source='address.building')
    ownership = serializers.ReadOnlyField(source='address.ownership')
    metro = serializers.ReadOnlyField(source='address.metro.name')

    class Meta:
        model = Realty
        fields = ("id",
                  "photos",
                  "price",
                  "number_of_rooms",
                  "realty_type",
                  "area",
                  "street",
                  "house_number",
                  "corpus",
                  "building",
                  "ownership",
                  "metro")


class ShortSaleSerializer(serializers.ModelSerializer):
    """Sale Short Detail Read Serializer."""

    realty = ShortRealtySerializer()

    class Meta:
        model = Sale
        fields = ("realty",)


class ShortRentSerializer(serializers.ModelSerializer):
    """Rent Short Detail Read Serializer."""

    realty = ShortRealtySerializer()

    class Meta:
        model = Rent
        fields = ("realty",)


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
    # realty_status = SlugRelatedField(
    #     slug_field="status",
    #     queryset=values_models.RealtyAdvStatus.objects.all(),
    # )
    sale = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()

    class Meta:
        model = realty_models.Realty
        exclude = ["changed_at", "realty_status",]
        # fields = "__all__"

    def get_sale(self, obj):
        """Return sales parameters."""
        if hasattr(obj, 'sale_profile'):
            return {
                "sales_parameters": specif_serializers.SalesParametersSerializer(
                    obj.sale_profile.sales_parameters
                ).data
            }
        return None

    def get_rent(self, obj):
        """Return rental_features."""
        if hasattr(obj, 'rent_profile'):
            return {
                "rental_features": specif_serializers.RentalFeaturesSerializer(
                    obj.rent_profile.rental_features
                ).data,
                "lease_payments": specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data
            }
        return None
