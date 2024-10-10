from rest_framework import serializers
from realty import models as realty_models
# from .models import City, Metro, Street, Address
from realty_addresses import models as address_models
from config import constants


# class CitySerializer(serializers.ModelSerializer):

#     class Meta:
#         model = City
#         fields = ("name",)


# class MetroSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Metro
#         fields = ("name",)


# class StreetSerializer(serializers.ModelSerializer):
#     city = CitySerializer()

#     class Meta:
#         model = Street
#         fields = (
#             "name",
#             "city"
#         )


# class AddressSerializer(serializers.ModelSerializer):
#     street = StreetSerializer()
#     metro = MetroSerializer()

#     class Meta:
#         model = Address
#         fields = (
#             "house_number",
#             "corpus",
#             "building",
#             "ownership",
#             "street",
#             "metro",
#             "minutes_to_metro",
#         )


class ZoneSerializer(serializers.ModelSerializer):
    """Zone Serializer."""

    name = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.Zone
        fields = ["name"]


class DistrictSerializer(serializers.ModelSerializer):
    """District Serilalizer."""

    name = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.District
        fields = ["name"]


class CitySerializer(serializers.ModelSerializer):
    """City Serilalizer."""

    name = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.City
        fields = ["name"]


class StreetReadSerializer(serializers.ModelSerializer):
    """Street Serializer."""

    zone = ZoneSerializer()
    district = DistrictSerializer()
    city = CitySerializer()

    class Meta:
        model = address_models.Street
        fields = "__all__"


class MetroSerializer(serializers.ModelSerializer):
    """Metro Serilalizer."""

    name = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.Metro
        fields = "__all__"


class AddressReadSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    street = StreetReadSerializer()
    metro = MetroSerializer()

    class Meta:
        model = address_models.Address
        fields = "__all__"


class MapPointsSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source='address.latitude')
    longitude = serializers.FloatField(source='address.longitude')

    class Meta:
        model = realty_models.Realty
        fields = "__all__"
