from django.db import transaction
from rest_framework import serializers

from config import constants
from realty import models as realty_models
from realty.serializers import serializers_realty as realty_serializers
from realty_specificities import models as specificities_models
from realty_values import models as values_models


class SaleReadSerializer(serializers.ModelSerializer):
    """Чтение продажи."""

    realty = realty_serializers.RealtyBaseSerializer()

    class Meta:
        model = realty_models.Sale
        exclude = ('sales_parameters',)


class SaleCreateSerializer(realty_serializers.RealtyCreateSerializer):
    """Создание продажи."""

    @transaction.atomic
    def create(self, validated_data):
        """Объявление и продажа создаются вместе: если что-то не сложилось,
        в базе не остаётся объявления без сделки."""
        sales_parameters = validated_data.pop('sales_parameters', None)
        realty = super().create(validated_data)

        if sales_parameters is None:
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

        realty_models.Sale.objects.create(
            realty=realty, sales_parameters=sales_parameters
        )
        return realty

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        return instance

    def to_representation(self, instance):
        if isinstance(instance, realty_models.Sale):
            return SaleReadSerializer(instance).data
        elif isinstance(instance, realty_models.Realty):
            return realty_serializers.RealtyBaseSerializer(instance).data
