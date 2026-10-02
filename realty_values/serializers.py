from rest_framework import serializers

from realty_values import models as values_models


class BuildingTypeSerializer(serializers.ModelSerializer):
    """Тип дома."""

    class Meta:
        model = values_models.BuildingType
        fields = '__all__'


class RoomsNumberSerializer(serializers.ModelSerializer):
    """Количество комнат."""

    class Meta:
        model = values_models.RoomsNumber
        fields = '__all__'


class RepairTypeSerilalizer(serializers.ModelSerializer):
    """Тип ремонта."""

    class Meta:
        model = values_models.RepairType
        fields = '__all__'


class BathroomTypeSerializer(serializers.ModelSerializer):
    """Тип санузла."""

    class Meta:
        model = values_models.BathroomType
        fields = '__all__'


class TradeParticipantSerializer(serializers.ModelSerializer):
    """Участник сделки."""

    class Meta:
        model = values_models.TradeParticipant
        fields = '__all__'


class HousingTypeSerializer(serializers.ModelSerializer):
    """Тип жилья."""

    class Meta:
        model = values_models.HousingType
        fields = '__all__'


class SaleTypeSerializer(serializers.ModelSerializer):
    """Тип продажи."""

    class Meta:
        model = values_models.SaleType
        fields = '__all__'
