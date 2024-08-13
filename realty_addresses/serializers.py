from rest_framework import serializers

from .models import City, Metro, Street, Address


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ("name",)


class MetroSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metro
        fields = ("name",)


class StreetSerializer(serializers.ModelSerializer):
    city = CitySerializer()

    class Meta:
        model = Street
        fields = (
            "name",
            "city"
        )


class AddressSerializer(serializers.ModelSerializer):
    street = StreetSerializer()
    metro = MetroSerializer()

    class Meta:
        model = Address
        fields = (
            "house_number",
            "corpus",
            "building",
            "ownership",
            "street",
            "metro",
            "minutes_to_metro",
        )
