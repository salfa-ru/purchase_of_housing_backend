from rest_framework import serializers

from config import constants
from realty import models as realty_models
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty.serializers import serializers_realty as realty_serializers
from realty_addresses import serializers as address_serializers
from realty_addresses import models as address_models


class SaleReadSerializer(serializers.ModelSerializer):
    """Sale Read Serializer."""

    realty = realty_serializers.RealtyBaseSerializer()

    class Meta:
        model = realty_models.Sale
        exclude = ('sales_parameters',)


class SaleCreateSerializer(realty_serializers.RealtyCreateSerializer):
    """Sale Create Serializer."""

    # realty = RealtyCreateSerializer(required=True)

    # class Meta:
    #     model = realty_models.Sale
    #     exclude = [
    #         "sales_parameters",
    #     ]

    def create(self, validated_data):
        realty = super().create(validated_data)
        validated_data['realty'] = realty
        # realty_data = validated_data.pop("realty", None)

        # if realty_data:
        #     realty_data["owner"] = self.context["request"].user
        #     realty = RealtyCreateSerializer(
        #         context=self.context
        #     )._create_realty(realty_data)
        #     validated_data["realty"] = realty

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
        if "realty" in validated_data:

            # присваиваем полученные аргументы переменным
            realty_data = validated_data.pop("realty", None)
            related_instance_realty = instance.realty
            address_data = realty_data.pop("address", None)
            about_building_data = realty_data.pop("about_building", None)
            about_apartment_data = realty_data.pop("about_apartment", None)
            common_characteristics_data = realty_data.pop("common_characteristics", None)

            # обновление поля address в модели realty
            if address_data and related_instance_realty.address:
                street_data = address_data.pop("street", None)
                metro_data = address_data.pop("metro", None)

                address_date_serializer = address_serializers.AddressCreateSerializer(
                    instance=instance.realty.address,
                    data=address_data,
                    partial=True
                )
                address_date_serializer.is_valid(raise_exception=True)
                address_date_serializer.save()

                # обновление поля street
                if street_data and related_instance_realty.address.street:
                    obj_instance = instance.realty.address.street
                    name = street_data.pop("name", obj_instance.name)
                    zone = street_data.pop("zone", obj_instance.zone)
                    district = street_data.pop("district", obj_instance.district)
                    city = street_data.pop("city", obj_instance.city)

                    street_data = {"name": name, "zone": zone, "district": district, "city": city}

                    obj_street, create = address_models.Street.objects.get_or_create(**street_data)
                    related_instance_realty.address.street = obj_street

                # обновление поля metro
                if metro_data and related_instance_realty.address.metro:
                    related_instance_realty.address.metro = metro_data

                related_instance_realty.address.save()

            # обновление поля about_building в модели realty
            if about_building_data and related_instance_realty.about_building:

                for attr, value in about_building_data.items():
                    setattr(related_instance_realty.about_building, attr, value)
                related_instance_realty.about_building.save()

            # обновление поля about_apartment в модели realty
            if about_apartment_data and related_instance_realty.about_apartment:

                for attr, value in about_apartment_data.items():
                    setattr(related_instance_realty.about_apartment, attr, value)
                related_instance_realty.about_apartment.save()

            # обновление поля common_characteristics в модели realty
            if common_characteristics_data and related_instance_realty.common_characteristics:

                for attr, value in common_characteristics_data.items():
                    setattr(related_instance_realty.common_characteristics, attr, value)
                related_instance_realty.common_characteristics.save()

            # обновление полей не имеющих dict значений в модели realty
            if realty_data and related_instance_realty:

                for attr, value in realty_data.items():
                    setattr(related_instance_realty, attr, value)
                related_instance_realty.save()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        if isinstance(instance, realty_models.Sale):
            return SaleReadSerializer(
                instance
            ).data
        elif isinstance(instance, realty_models.Realty):
            return realty_serializers.RealtyBaseSerializer(
                instance
            ).data

        # return SaleReadSerializer(
        #     instance
        # ).data


class ShortSaleSerializer(serializers.ModelSerializer):
    """Sale Short Detail Read Serializer."""

    realty = realty_serializers.ShortRealtySerializer()

    class Meta:
        model = realty_models.Sale
        fields = ("realty",)
