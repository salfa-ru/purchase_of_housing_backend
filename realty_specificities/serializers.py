from django.core import validators
from django.core.exceptions import ValidationError
from rest_framework import serializers

from config import constants
from realty_specificities import models as spec_models
from realty_values import models as values_models
from realty_values import serializers as values_serializers


class AboutBuildingSerializer(serializers.ModelSerializer):
    """О доме."""

    type = values_serializers.BuildingTypeSerializer()

    class Meta:
        model = spec_models.AboutBuilding
        fields = '__all__'


class AboutBuildingCreateSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.BuildingType.objects.all(),
        required=False,
    )

    class Meta:
        model = spec_models.AboutBuilding
        fields = '__all__'


class AboutApartmentSerializer(serializers.ModelSerializer):
    """О квартире."""

    number_of_rooms = values_serializers.RoomsNumberSerializer()

    class Meta:
        model = spec_models.AboutApartment
        fields = '__all__'


class AboutApartmentCreateSerializer(serializers.ModelSerializer):
    """Создание данных о квартире."""

    number_of_rooms = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RoomsNumber.objects.all(),
        required=True,
    )
    area = serializers.FloatField(
        required=True,
        validators=[
            validators.MinValueValidator(constants.MIN_ROOM_AREA),
            validators.MaxValueValidator(constants.MAX_ROOM_AREA),
        ],
    )
    floor = serializers.IntegerField(
        validators=(
            validators.MinValueValidator(constants.MIN_FLOOR),
            validators.MaxValueValidator(constants.MAX_FLOOR),
        )
    )
    floors_number = serializers.IntegerField(
        validators=(
            validators.MinValueValidator(constants.MIN_FLOOR),
            validators.MaxValueValidator(constants.MAX_FLOOR),
        )
    )

    class Meta:
        model = spec_models.AboutApartment
        fields = '__all__'

    def validate(self, data):
        floor = data.get('floor')
        floors_number = data.get('floors_number')

        if self.instance:
            if floor is None:
                floor = self.instance.floor
            if floors_number is None:
                floors_number = self.instance.floors_number

        if floor and floors_number and floor > floors_number:
            raise ValidationError(
                'Этаж не может быть больше, чем общая этажность здания!'
            )

        return data


class CommonCharacteristicsCreateSerializer(serializers.ModelSerializer):
    """Создание общих характеристик."""

    repair_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RepairType.objects.all(),
        required=False,
    )
    bathroom = serializers.PrimaryKeyRelatedField(
        queryset=values_models.BathroomType.objects.all(),
        required=False,
    )

    class Meta:
        model = spec_models.CommonCharacteristics
        fields = '__all__'


class CommonCharacteristicsSerializer(serializers.ModelSerializer):
    """Общие характеристики."""

    repair_type = values_serializers.RepairTypeSerilalizer()
    bathroom = values_serializers.BathroomTypeSerializer()

    class Meta:
        model = spec_models.CommonCharacteristics
        fields = '__all__'


class RentalFeaturesCreateSerializer(serializers.ModelSerializer):
    """Создание условий аренды."""

    class Meta:
        model = spec_models.RentalFeatures
        fields = '__all__'


class LeasePaymentsCreateSerializer(serializers.ModelSerializer):
    """Создание платежей по аренде."""

    counters_payment = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeParticipant.objects.all(),
        required=False,
    )
    communal_payment = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeParticipant.objects.all(),
        required=False,
    )
    deposit = serializers.IntegerField(
        required=False,
    )

    class Meta:
        model = spec_models.LeasePayments
        fields = '__all__'

    def validate_deposit(self, value):
        """Проверка размера залога."""
        if value < 0:
            raise serializers.ValidationError('Залог не может быть отрицательным.')
        return value


class LeasePaymentsSerializer(serializers.ModelSerializer):
    """Платежи по аренде."""

    counters_payment = values_serializers.TradeParticipantSerializer()
    communal_payment = values_serializers.TradeParticipantSerializer()

    class Meta:
        model = spec_models.LeasePayments
        fields = '__all__'


class SalesParametersSerializer(serializers.ModelSerializer):
    """Параметры продажи."""

    housing_type = values_serializers.HousingTypeSerializer()
    sale_type = values_serializers.SaleTypeSerializer()

    class Meta:
        model = spec_models.SalesParameters
        fields = '__all__'


class RentalFeaturesSerializer(serializers.ModelSerializer):
    """Условия аренды."""

    class Meta:
        model = spec_models.RentalFeatures
        fields = [
            'fridge',
            'internet',
            'conditioner',
            'tv',
            'dishwasher',
            'washing_machine',
            'garbage_chute',
            'kids_allowed',
            'animals_allowed',
        ]
