from rest_framework import serializers

from realty import models as realty_models
from realty_addresses import models as address_models
from realty_specificities import models as specificities_models
from realty.serializers import serializers_realty as realty_serializers
from realty_addresses import serializers as address_serializers
from realty_specificities import serializers as specif_serializers


class RentReadSerializer(serializers.ModelSerializer):
    """Rent Read Serializer."""

    realty = realty_serializers.RealtyBaseSerializer()

    class Meta:
        model = realty_models.Rent
        exclude = ('rental_features', 'lease_payments',)


class RentCreateSerializer(serializers.ModelSerializer):
    """Rent Create Serializer."""

    realty = realty_serializers.RealtyCreateSerializer(required=True)
    rental_features = specif_serializers.RentalFeaturesSerilalizer(
        required=False
    )
    lease_payments = specif_serializers.LeasePaymentsCreateSerializer(
        required=False
    )

    def create(self, validated_data):
        realty_data = validated_data.pop("realty", None)
        rental_features_data = validated_data.pop("rental_features", None)
        lease_payments_data = validated_data.pop("lease_payments", None)

        if realty_data:
            realty_data["owner"] = self.context["request"].user
            realty = realty_serializers.RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data["realty"] = realty

        rental_features = (specificities_models.RentalFeatures.objects.create(
            **rental_features_data) if rental_features_data else None)
        validated_data["rental_features"] = rental_features

        lease_payments = (specificities_models.LeasePayments.objects.create(
            **lease_payments_data) if lease_payments_data else None)
        validated_data["lease_payments"] = lease_payments
        validated_data.pop("owner", None)
        rent = realty_models.Rent.objects.create(**validated_data)
        return rent

    def update(self, instance, validated_data):
        print(f"Это Instance 2 : {instance.realty.__dict__}")
        print(f"Это validated_data : {validated_data}")

        # Обновление модели realty через модель Rent
        if "realty" in validated_data:
            realty_data = validated_data.pop("realty", None)
            realty_serializer = realty_serializers.RealtyCreateSerializer(
                instance=instance.realty,
                data=realty_data,
                partial=True
            )
            realty_serializer.is_valid(raise_exception=True)
            realty_serializer.save()
            print(f"Это Instance : {instance.realty.__dict__}")


            # присваиваем полученные аргументы переменным

            # related_instance_realty = instance.realty
            # address_data = realty_data.pop("address", None)
            # about_building_data = realty_data.pop("about_building", None)
            # about_apartment_data = realty_data.pop("about_apartment", None)
            # common_characteristics_data = realty_data.pop("common_characteristics", None)
            #
            # # обновление поля address в модели realty
            # if address_data and related_instance_realty.address:
            #     street_data = address_data.pop("street", None)
            #     metro_data = address_data.pop("metro", None)
            #
            #     address_date_serializer = address_serializers.AddressCreateSerializer(
            #         instance=instance.realty.address,
            #         data=address_data,
            #         partial=True
            #     )
            #     address_date_serializer.is_valid(raise_exception=True)
            #     address_date_serializer.save()
            #
            #     # обновление поля street
            #     if street_data and related_instance_realty.address.street:
            #         obj_instance = instance.realty.address.street
            #         name = street_data.pop("name", obj_instance.name)
            #         zone = street_data.pop("zone", obj_instance.zone)
            #         district = street_data.pop("district", obj_instance.district)
            #         city = street_data.pop("city", obj_instance.city)
            #
            #         street_data = {"name": name, "zone": zone, "district": district, "city": city}
            #
            #         obj_street, create = address_models.Street.objects.get_or_create(**street_data)
            #         related_instance_realty.address.street = obj_street
            #
            #     # обновление поля metro
            #     if metro_data and related_instance_realty.address.metro:
            #         related_instance_realty.address.metro = metro_data
            #
            #     related_instance_realty.address.save()
            #
            # # обновление поля about_building в модели realty
            # if about_building_data and related_instance_realty.about_building:
            #
            #     for attr, value in about_building_data.items():
            #         setattr(related_instance_realty.about_building, attr, value)
            #     related_instance_realty.about_building.save()
            #
            # # обновление поля about_apartment в модели realty
            # if about_apartment_data and related_instance_realty.about_apartment:
            #
            #     for attr, value in about_apartment_data.items():
            #         setattr(related_instance_realty.about_apartment, attr, value)
            #     related_instance_realty.about_apartment.save()
            #
            # # обновление поля common_characteristics в модели realty
            # if common_characteristics_data and related_instance_realty.common_characteristics:
            #
            #     for attr, value in common_characteristics_data.items():
            #         setattr(related_instance_realty.common_characteristics, attr, value)
            #     related_instance_realty.common_characteristics.save()
            #
            # # обновление полей не имеющих dict значений в модели realty
            # if realty_data and related_instance_realty:
            #
            #     for attr, value in realty_data.items():
            #         setattr(related_instance_realty, attr, value)
            #     related_instance_realty.save()

        # Обновление поля rental_features
        if "rental_features" in validated_data:
            rental_features_data = validated_data.pop('rental_features', None)
            related_instance_rental_features = instance.rental_features

            if related_instance_rental_features:
                for attr, value in rental_features_data.items():
                    setattr(instance.rental_features, attr, value)
                # related_instance_rental_features.save()

        # Обновление поля lease_payments
        if "lease_payments" in validated_data:
            lease_payments_data = validated_data.pop('lease_payments', None)
            related_instance_lease_payments = instance.lease_payments

            if related_instance_lease_payments:
                for attr, value in lease_payments_data.items():
                    setattr(related_instance_lease_payments, attr, value)
                related_instance_lease_payments.save()
        instance.save()
        print(f"instance :   {instance}")

        return instance

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class ShortRentSerializer(serializers.ModelSerializer):
    """Rent Short Detail Read Serializer."""

    realty = realty_serializers.ShortRealtySerializer()

    class Meta:
        model = realty_models.Rent
        fields = ("realty",)
