from rest_framework import serializers

from config import constants
from config.constants import MAX_MINUTES_TO_METRO
from realty import models as realty_models
from realty_addresses import models as address_models


class ZoneSerializer(serializers.ModelSerializer):
    """Район."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.Zone
        fields = ['name']


class DistrictSerializer(serializers.ModelSerializer):
    """Округ."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.District
        fields = ['name']


class CitySerializer(serializers.ModelSerializer):
    """Город."""

    name = serializers.CharField(
        max_length=constants.CHAR_LENGTH,
        required=True,
    )

    class Meta:
        model = address_models.City
        fields = ['name']


class StreetReadSerializer(serializers.ModelSerializer):
    """Чтение улицы."""

    zone = ZoneSerializer()
    district = DistrictSerializer()
    city = CitySerializer()

    class Meta:
        model = address_models.Street
        fields = '__all__'


class StreetCreateSerializer(serializers.ModelSerializer):
    """Создание улицы."""

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

    class Meta:
        model = address_models.Street
        fields = '__all__'


class MetroSerializer(serializers.ModelSerializer):
    """Станция метро."""

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
    """Чтение адреса."""

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


class AddressCreateSerializer(serializers.ModelSerializer):
    """Создание адреса."""

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
        required=False,
        allow_null=True,
    )

    minutes_to_metro = serializers.IntegerField(required=False, allow_null=True)

    def validate_minutes_to_metro(self, value):
        """Валидация для minutes_to_metro, чтобы значение было <= 59."""
        if value is not None and value > MAX_MINUTES_TO_METRO:
            raise serializers.ValidationError(
                f"Значение 'minutes_to_metro' не может быть больше "
                f'{MAX_MINUTES_TO_METRO}.'
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

        validated_data['metro'] = metro

        address, _ = address_models.Address.objects.get_or_create(**validated_data)
        return address

    def update(self, instance, validated_data):
        street_data = validated_data.pop('street', None)
        metro = validated_data.pop('metro', None)

        if street_data:
            street_serializer = StreetCreateSerializer(
                instance=instance.street, data=street_data, partial=True
            )
            street_serializer.is_valid(raise_exception=True)
            street_serializer.save()

        if metro is not None:
            instance.metro = metro
        else:
            instance.metro = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    class Meta:
        model = address_models.Address
        fields = '__all__'
