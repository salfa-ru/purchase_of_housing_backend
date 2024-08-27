from rest_framework import serializers

from realty_addresses import models as address_models
from config import constants


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


class StreetCreateSerializer(serializers.ModelSerializer):
    """Street Create Serializer."""

    name = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    zone = ZoneSerializer(required=False)
    district = DistrictSerializer(required=False)
    city = CitySerializer(required=True)

    def create(self, validated_data):
        zone_data = validated_data.pop("zone", None)
        district_data = validated_data.pop("district", None)
        city_data = validated_data.pop("city", None)

        if zone_data:
            zone_serializer = ZoneSerializer(data=zone_data)
            zone_serializer.is_valid(raise_exception=True)
            zone = zone_serializer.save()
            validated_data["zone"] = zone
        if district_data:
            district_serializer = DistrictSerializer(data=district_data)
            district_serializer.is_valid(raise_exception=True)
            district = district_serializer.save()
            validated_data["district"] = district
        if city_data:
            city_serializer = CitySerializer(data=city_data)
            city_serializer.is_valid(raise_exception=True)
            city = city_serializer.save()
            validated_data["city"] = city

        street = address_models.Street.objects.create(**validated_data)
        return street

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


class AddressCreateSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    house_number = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    street = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    corpus = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    building = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    ownership = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    map_point = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    street = StreetCreateSerializer(required=True)
    metro = MetroSerializer(required=False)

    def create(self, validated_data):
        street_data = validated_data.pop("street", None)
        metro_data = validated_data.pop("metro", None)

        if street_data:
            street_serializer = StreetCreateSerializer(
                data=street_data
            )
            street_serializer.is_valid(
                raise_exception=True
            )
            street = street_serializer.save()
            validated_data["street"] = street

        if metro_data:
            metro_serializer = MetroSerializer(
                data=metro_data
            )
            metro_serializer.is_valid(
                raise_exception=True
            )
            metro = metro_serializer.save()
            validated_data["metro"] = metro

        address = address_models.Address.objects.create(
            **validated_data
        )
        return address

    class Meta:
        model = address_models.Address
        fields = "__all__"
