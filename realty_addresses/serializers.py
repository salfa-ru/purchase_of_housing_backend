from rest_framework import serializers

from config import constants
from config.constants import MAX_MINUTES_TO_METRO
from realty import models as realty_models
from realty_addresses import models as address_models


class ZoneSerializer(serializers.ModelSerializer):
    """Zone Serializer."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.Zone
        fields = ['name']


class DistrictSerializer(serializers.ModelSerializer):
    """District Serilalizer."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.District
        fields = ['name']


class CitySerializer(serializers.ModelSerializer):
    """City Serilalizer."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.City
        fields = ['name']


class StreetReadSerializer(serializers.ModelSerializer):
    """Street Serializer."""

    zone = ZoneSerializer()
    district = DistrictSerializer()
    city = CitySerializer()

    class Meta:
        model = address_models.Street
        fields = '__all__'


class StreetCreateSerializer(serializers.ModelSerializer):
    """Street Create Serializer."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )
    zone = serializers.PrimaryKeyRelatedField(
        queryset=address_models.Zone.objects.all(),
        required=False,
        allow_null=True,
    )
    district = serializers.PrimaryKeyRelatedField(
        queryset=address_models.District.objects.all(),
        required=False,
        allow_null=True,
    )
    city = serializers.PrimaryKeyRelatedField(
        queryset=address_models.City.objects.all(), required=True
    )

    # def create(self, validated_data):  # DONE
    #     city_data = validated_data.pop("city", None)
    #     zone_data = validated_data.pop("zone", None)
    #     district_data = validated_data.pop("district", None)

    #     if city_data:
    #         city = address_models.Street.objects.get(id=city['id'])
    #     else:
    #         city = None

    #     if zone_data:
    #         zone = address_models.Zone.objects.get(id=zone_data['id'])
    #     else:
    #         zone = None

    #     if district_data:
    #         district = address_models.District.objects.get(id=district_data['id'])
    #     else:
    #         district = None

    #     street = address_models.Street.objects.create(
    #         zone=zone,
    #         district=district,
    #         city=city)
    #     return street

    # def create(self, validated_data):
    #     zone_data = validated_data.pop("zone", None)
    #     district_data = validated_data.pop("district", None)
    #     city_data = validated_data.pop("city", None)

    #     zone, _ = (address_models.Zone.objects.get_or_create(
    #         **zone_data) if zone_data else None)
    #     validated_data["zone"] = zone

    #     district = (address_models.District.objects.create(
    #         **district_data) if district_data else None)
    #     validated_data["district"] = district

    #     if city_data:
    #     #     city, _ = address_models.City.objects.get_or_create(**city_data)
    #     #     validated_data["city"] = city
    #     # street, _ = address_models.Street.objects.get_or_create(
    #     #     **validated_data
    #     # )
    #         validated_data["city"] = city_data
    #     street, _ = address_models.Street.objects.get_or_create(
    #         **validated_data
    #     )
    #     return street

    class Meta:
        model = address_models.Street
        fields = '__all__'


class MetroSerializer(serializers.ModelSerializer):
    """Metro Serilalizer."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    color = serializers.CharField(source='line.color', read_only=True)
    line_name = serializers.CharField(source='line.name', read_only=True)
    line_name_full = serializers.CharField(source='line.name_full', read_only=True)

    class Meta:
        model = address_models.Metro
        fields = ['id', 'name', 'name_full', 'color', 'line_name', 'line_name_full']


class AddressReadSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    street = StreetReadSerializer()
    metro = MetroSerializer()

    class Meta:
        model = address_models.Address
        fields = '__all__'


class MapPointsSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source='address.latitude')
    longitude = serializers.FloatField(source='address.longitude')

    class Meta:
        model = realty_models.Realty
        fields = ['id', 'latitude', 'longitude']


class MapPointsRequestSerializer(serializers.Serializer):
    top_left_latitude = serializers.FloatField(required=True)
    top_left_longitude = serializers.FloatField(required=True)
    bottom_right_latitude = serializers.FloatField(required=True)
    bottom_right_longitude = serializers.FloatField(required=True)


class GetAnnouncementsInMapPointRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)


class GetAnnouncementsInMapPoint(serializers.ModelSerializer):
    street = serializers.CharField(source='address.street.name')
    house_number = serializers.CharField(source='address.house_number')
    corpus = serializers.CharField(source='address.corpus')
    building = serializers.CharField(source='address.building')
    number_of_rooms = serializers.CharField(
        source='about_apartment.number_of_rooms.number_of_rooms'
    )
    realty_type = serializers.CharField(source='realty_type.type')

    class Meta:
        model = realty_models.Realty
        fields = [
            'realty_type',
            'price',
            'street',
            'number_of_rooms',
            'house_number',
            'corpus',
            'building',
        ]


class AddressCreateSerializer(serializers.ModelSerializer):
    """Address Serializer."""

    house_number = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )
    corpus = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=False,
        allow_null=True,
    )
    building = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=False,
        allow_null=True,
    )
    ownership = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=False,
        allow_null=True,
    )
    latitude = serializers.FloatField(
        required=True,
    )
    longitude = serializers.FloatField(
        required=True,
    )
    street = StreetCreateSerializer(required=True)
    metro = serializers.PrimaryKeyRelatedField(
        queryset=address_models.Metro.objects.all(),
        required=False,  # Необязательно для создания/обновления
        allow_null=True,
    )

    minutes_to_metro = serializers.IntegerField(required=False, allow_null=True)

    def validate_minutes_to_metro(self, value):
        """Валидация для minutes_to_metro, чтобы значение было <= 59."""
        if value is not None and value > MAX_MINUTES_TO_METRO:
            raise serializers.ValidationError(
                f"Значение 'minutes_to_metro' не может быть больше {MAX_MINUTES_TO_METRO}."
            )
        return value

    def create(self, validated_data):
        street_data = validated_data.pop('street', None)
        metro = validated_data.pop('metro', None)

        if street_data:
            street_serializer = StreetCreateSerializer(data=street_data)

            if 'city' in street_data:
                city = street_data['city']
                street_data['city'] = city.id
            if 'zone' in street_data and street_data['zone'] is not None:
                zone = street_data['zone']
                street_data['zone'] = zone.id
            else:
                street_data['zone'] = None
            if 'district' in street_data and street_data['district'] is not None:
                district = street_data['district']
                street_data['district'] = district.id
            else:
                street_data['district'] = None

            street_serializer.is_valid(raise_exception=True)
            street = street_serializer.save()
            validated_data['street'] = street

        validated_data['metro'] = metro  # Связываем метро по id

        address, _ = address_models.Address.objects.get_or_create(**validated_data)
        return address

    def update(self, instance, validated_data):
        street_data = validated_data.pop('street', None)
        metro = validated_data.pop('metro', None)

        # Обновление улицы через StreetCreateSerializer
        if street_data:
            street_serializer = StreetCreateSerializer(
                instance=instance.street, data=street_data, partial=True
            )
            street_serializer.is_valid(raise_exception=True)
            street_serializer.save()

        # Обновление метро
        if metro is not None:
            instance.metro = metro
        else:
            instance.metro = None

        # Обновление остальных полей Address
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    class Meta:
        model = address_models.Address
        fields = '__all__'
