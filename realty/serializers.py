from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from .models import Realty, Sale, Rent
from realty_photos.serializers import RealtyPhotoSerializer
from realty import models as realty_models
from realty_values import models as values_models
from realty_addresses import serializers as address_serializers
from realty_specificities import serilalizers as specif_serializers


class ShortRealtySerializer(serializers.ModelSerializer):
    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    number_of_rooms = serializers.CharField(
        source="about_apartment.number_of_rooms.number_of_rooms"
    )
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
    realty = ShortRealtySerializer()

    class Meta:
        model = Sale
        fields = ("realty",)


class ShortRentSerializer(serializers.ModelSerializer):
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
    realty_status = SlugRelatedField(
        slug_field="status",
        queryset=values_models.RealtyAdvStatus.objects.all(),
    )

    class Meta:
        model = realty_models.Realty
        # exclude = ["published_at", "changed_at"]
        fields = "__all__"

# class RealtySerializer(serializers.ModelSerializer):
#     trade_type = serializers.ReadOnlyField()

#     class Meta:
#         model = Realty
#         fields = ('id',
#                   'realty_type',
#                   'address',
#                   'description',
#                   'price',
#                   'trade_type',
#                   'published_at',
#                   'about_apartment',
#                   'owner')
