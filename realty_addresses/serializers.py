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


MAP_LATITUDE_ORDER = (
    'Верхний левый угол должен быть севернее нижнего правого: '
    'top_left_latitude не может быть меньше bottom_right_latitude.'
)
MAP_LONGITUDE_ORDER = (
    'Верхний левый угол должен быть западнее нижнего правого: '
    'top_left_longitude не может быть больше bottom_right_longitude.'
)


def latitude_field():
    return serializers.FloatField(required=True, min_value=-90, max_value=90)


def longitude_field():
    return serializers.FloatField(required=True, min_value=-180, max_value=180)


class MapPointsRequestSerializer(serializers.Serializer):
    """Видимая часть карты: верхний левый и нижний правый углы."""

    top_left_latitude = latitude_field()
    top_left_longitude = longitude_field()
    bottom_right_latitude = latitude_field()
    bottom_right_longitude = longitude_field()

    def validate(self, data):
        errors = {}
        if data['top_left_latitude'] < data['bottom_right_latitude']:
            errors['top_left_latitude'] = MAP_LATITUDE_ORDER
        if data['top_left_longitude'] > data['bottom_right_longitude']:
            errors['top_left_longitude'] = MAP_LONGITUDE_ORDER
        if errors:
            raise serializers.ValidationError(errors)
        return data


class GetAnnouncementsInMapPointRequestSerializer(serializers.Serializer):
    latitude = latitude_field()
    longitude = longitude_field()


STREET_FIELDS = ('name', 'city', 'zone', 'district')
ADDRESS_FIELDS = (
    'house_number',
    'corpus',
    'building',
    'ownership',
    'latitude',
    'longitude',
    'metro',
    'minutes_to_metro',
)


def resolve_street(street_data, current=None):
    """Подбирает улицу под переданные данные, недостающее берёт у текущей.

    Улица — общий справочник: на одну и ту же улицу ссылаются разные
    объявления. Поэтому запись не переписывается, а подбирается готовая или
    заводится новая. Иначе правка одного адреса переименует улицу у всех
    соседних объявлений и обнулит у них район с округом."""
    values = {
        field: street_data[field]
        if field in street_data
        else (getattr(current, field) if current is not None else None)
        for field in STREET_FIELDS
    }
    street, _ = address_models.Street.objects.get_or_create(**values)
    return street


def resolve_address(address_data, current=None):
    """Подбирает адрес под переданные данные, недостающее берёт у текущего.

    Адрес тоже общий: одна запись может стоять у нескольких объявлений."""
    if 'street' in address_data and address_data['street'] is not None:
        street = resolve_street(
            address_data['street'], current.street if current is not None else None
        )
    else:
        street = current.street if current is not None else None

    values = {
        field: address_data[field]
        if field in address_data
        else (getattr(current, field) if current is not None else None)
        for field in ADDRESS_FIELDS
    }
    values['street'] = street
    address, _ = address_models.Address.objects.get_or_create(**values)
    return address


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
    latitude = latitude_field()
    longitude = longitude_field()
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
        return resolve_address(validated_data)

    def update(self, instance, validated_data):
        """Возвращает подходящий адрес, а старую запись не трогает: она может
        стоять у другого объявления."""
        return resolve_address(validated_data, instance)

    class Meta:
        model = address_models.Address
        fields = '__all__'
