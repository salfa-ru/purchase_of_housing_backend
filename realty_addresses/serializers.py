from rest_framework import serializers

from realty_addresses import models as address_models


class ZoneSerilaizers(serializers.ModelSerializer):
    """Zone Serializer."""

    class Meta:
        model = address_models.Zone
        fields = "__all__"


class DistrictSerializer(serializers.ModelSerializer):
    """District Serilalizer."""

    class Meta:
        model = address_models.District
        fields = "__all__"


class CitySerializer(serializers.ModelSerializer):
    """City Serilalizer."""

    class Meta:
        model = address_models.City
        fields = "__all__"


class StreetSerializer(serializers.ModelSerializer):
    """Street Serializer."""

    zone = ZoneSerilaizers()
    district = DistrictSerializer()
    city = CitySerializer()

    class Meta:
        model = address_models.Street
        fields = "__all__"


class MetroSerializer(serializers.ModelSerializer):
    """Metro Serilalizer."""

    class Meta:
        model = address_models.Metro
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    street = StreetSerializer()
    metro = MetroSerializer()

    class Meta:
        model = address_models.Address
        fields = "__all__"
