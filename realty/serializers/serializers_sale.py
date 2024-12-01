from rest_framework import serializers

from config import constants
from realty import models as realty_models
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty.serializers import serializers_realty as realty_serializers


class SaleReadSerializer(serializers.ModelSerializer):
    """Sale Read Serializer."""

    realty = realty_serializers.RealtyBaseSerializer()

    class Meta:
        model = realty_models.Sale
        exclude = ('sales_parameters',)


class SaleCreateSerializer(realty_serializers.RealtyCreateSerializer):
    """Sale Create Serializer."""

    def create(self, validated_data):
        # Создаем данные Realty через родительский метод
        realty = super().create(validated_data)
        validated_data['realty'] = realty

        if "sales_parameters" not in validated_data:
            housing_type, _ = values_models.HousingType.objects.get_or_create(
                type=constants.HOUSING_TYPE
            )
            sale_type, _ = values_models.SaleType.objects.get_or_create(
                type=constants.SALE_TYPE
            )
            sales_parameters, _ = (
                specificities_models.SalesParameters.objects.get_or_create(
                    housing_type=housing_type, sale_type=sale_type
                )
            )
            validated_data["sales_parameters"] = sales_parameters

        validated_data.pop("owner", None)
        validated_data = {
            'realty': realty,
            'sales_parameters': sales_parameters
        }
        realty_models.Sale.objects.create(**validated_data)
        return realty

    def update(self, instance, validated_data):
        # Обновляем данные Realty через родительский метод
        instance = super().update(instance, validated_data)

        return instance

    def to_representation(self, instance):

        if isinstance(instance, realty_models.Sale):
            return SaleReadSerializer(
                instance
            ).data
        elif isinstance(instance, realty_models.Realty):
            return realty_serializers.RealtyBaseSerializer(
                instance
            ).data


class ShortSaleSerializer(serializers.ModelSerializer):
    """Sale Short Detail Read Serializer."""

    realty = realty_serializers.ShortRealtySerializer()

    class Meta:
        model = realty_models.Sale
        fields = ("realty",)
