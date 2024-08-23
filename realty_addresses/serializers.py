from rest_framework import serializers

from realty_addresses import models as address_models


class ZoneSerializer(serializers.ModelSerializer):
    """Zone Serializer."""

    class Meta:
        model = address_models.Zone
        fields = ["name"]  # Убедитесь, что 'name' - поле в модели Zone


class DistrictSerializer(serializers.ModelSerializer):
    """District Serilalizer."""

    class Meta:
        model = address_models.District
        fields = ["name"]  # Убедитесь, что 'name' - поле в модели District


class CitySerializer(serializers.ModelSerializer):
    """City Serilalizer."""

    class Meta:
        model = address_models.City
        fields = ["name"]  # Убедитесь, что 'name' - поле в модели City


class StreetSerializer(serializers.ModelSerializer):
    """Street Serializer."""

    zone = ZoneSerializer()
    district = DistrictSerializer()
    city = CitySerializer()

    class Meta:
        model = address_models.Street
        fields = "__all__"


# class StreetCreateSerializer(serializers.ModelSerializer):
#     """Street Create Serializer."""

#     zone = ZoneSerializer(required=False)
#     district = DistrictSerializer(required=False)
#     city = CitySerializer(required=True)

#     def create(self, validated_data):
#         zone_data = validated_data.pop("zone", None)
#         district_data = validated_data.pop("district", None)
#         city_data = validated_data.pop("city", None)

#         if zone_data:
#             zone = ZoneSerializer(data=zone_data).save()
#             validated_data["zone"] = zone
#         if district_data:
#             district = DistrictSerializer(data=district_data).save()
#             validated_data["district"] = district
#         if city_data:
#             city = CitySerializer(data=city_data).save()
#             validated_data["city"] = city

#         street = address_models.Street.objects.create(**validated_data)
#         return street

#     class Meta:
#         model = address_models.Street
#         fields = "__all__"


class StreetCreateSerializer(serializers.ModelSerializer):
    """Street Create Serializer."""

    zone = ZoneSerializer(required=False)
    district = DistrictSerializer(required=False)
    city = CitySerializer(required=True)

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


# class AddressCreateSerializer(serializers.ModelSerializer):
#     """Address Serializer."""

#     street = StreetCreateSerializer(required=True)
#     metro = MetroSerializer(required=False)

#     def create(self, validated_data):
#         street_data = validated_data.pop("street", None)
#         metro_data = validated_data.pop("metro", None)
#         if street_data:
#             street = address_models.Street.objects.create(**street_data)
#             validated_data["street"] = street
#         if metro_data:
#             metro = address_models.Metro.objects.create(**metro_data)
#             validated_data["metro"] = metro
#         address = address_models.Address.objects.create(**validated_data)
#         return address

#     class Meta:
#         model = address_models.Address
#         fields = "__all__"


class AddressCreateSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    street = StreetCreateSerializer(required=True)
    metro = MetroSerializer(required=False)

    def create(self, validated_data):
        street_data = validated_data.pop("street")
        print("" + street_data)
        zone_data = street_data.pop("zone", None)
        print(zone_data)
        district_data = street_data.pop("district", None)
        print(zone_data)
        city_data = street_data.pop("city", None)
        print(zone_data)

        # Создание экземпляра City
        if city_data:
            city_serializer = CitySerializer(data=city_data)
            city_serializer.is_valid(raise_exception=True)
            city = city_serializer.save()
            street_data["city"] = city

        # Создание экземпляра District
        if district_data:
            district_serializer = DistrictSerializer(data=district_data)
            district_serializer.is_valid(raise_exception=True)
            district = district_serializer.save()
            street_data["district"] = district

        # Создание экземпляра Zone
        if zone_data:
            zone_serializer = ZoneSerializer(data=zone_data)
            zone_serializer.is_valid(raise_exception=True)
            zone = zone_serializer.save()
            street_data["zone"] = zone

        # Создание экземпляра Street
        street_serializer = StreetCreateSerializer(data=street_data)
        street_serializer.is_valid(raise_exception=True)
        street = street_serializer.save()

        validated_data["street"] = street

        # Создание экземпляра Metro, если он есть
        metro_data = validated_data.pop("metro", None)
        if metro_data:
            metro_serializer = MetroSerializer(data=metro_data)
            metro_serializer.is_valid(raise_exception=True)
            metro = metro_serializer.save()
            validated_data["metro"] = metro

        # Создание экземпляра Address
        address = address_models.Address.objects.create(**validated_data)
        return address

    class Meta:
        model = address_models.Address
        fields = "__all__"
