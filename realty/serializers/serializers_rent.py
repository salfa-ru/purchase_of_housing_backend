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

        # Обновление модели realty через модель Rent
        if "realty" in validated_data:
            realty_data = validated_data.pop("realty", None)

            # realty_data["realty_type"] = realty_data["realty_type"].pk if realty_data.get("realty_type") else
            # realty_data["address"]["street"]["zone"] = realty_data["address"]["street"]["zone"].pk
            # realty_data["address"]["street"]["district"] = realty_data["address"]["street"]["district"].pk
            # realty_data["address"]["street"]["city"] = realty_data["address"]["street"]["city"].pk
            # realty_data["address"]["metro"] = realty_data["address"]["metro"].pk
            # realty_data["about_building"]["type"] = realty_data["about_building"]["type"].pk
            # realty_data["about_apartment"]["number_of_rooms"] = realty_data["about_apartment"]["number_of_rooms"].pk
            # realty_data["common_characteristics"]["repair_type"] = realty_data["common_characteristics"][
            #     "repair_type"].pk
            # realty_data["common_characteristics"]["bathroom"] = realty_data["common_characteristics"]["bathroom"].pk
            # realty_data["owner_type"] = realty_data["owner_type"].pk
            # realty_data["communication_method"] = realty_data["communication_method"].pk

            fields_to_convert = [
                ("realty_type",),
                ("address", "street", "zone"),
                ("address", "street", "district"),
                ("address", "street", "city"),
                ("address", "metro"),
                ("about_building", "type"),
                ("about_apartment", "number_of_rooms"),
                ("common_characteristics", "repair_type"),
                ("common_characteristics", "bathroom"),
                ("owner_type",),
                ("communication_method",)
            ]

            for field in fields_to_convert:

                current_data = realty_data
                if "address" in current_data:
                    # Обработка metro
                    current_data["address"]["metro"] = current_data["address"].get(
                        "metro", instance.realty.address.metro.pk if instance.realty.address.metro else None
                    )

                    if "street" in current_data["address"]:
                        # Обработка street
                        street_data = current_data["address"]["street"]

                        street_data["zone"] = street_data.get(
                            "zone",
                            instance.realty.address.street.zone.pk if instance.realty.address.street.zone else None
                        )
                        street_data["district"] = street_data.get(
                            "district",
                            instance.realty.address.street.district.pk if instance.realty.address.street.district else None
                        )

                for key in field[:-1]:

                    if not isinstance(current_data, dict) or key not in current_data:
                        break
                    current_data = current_data[key]

                if (
                        isinstance(current_data, dict)
                        and field[-1] in current_data
                        and hasattr(current_data[field[-1]], 'pk')
                ):
                    current_data[field[-1]] = current_data[field[-1]].pk

            realty_serializer = realty_serializers.RealtyCreateSerializer(
                instance=instance.realty,
                data=realty_data,
                partial=True
            )
            realty_serializer.is_valid(raise_exception=True)
            realty_serializer.save()

        def update_related(instance_field, related_data):
            if instance_field and related_data:
                for attr, value in related_data.items():
                    setattr(instance_field, attr, value)
                instance_field.save()

        # Обновление rental_features
        update_related(instance.rental_features, validated_data.pop("rental_features", None))

        # Обновление lease_payments
        update_related(instance.lease_payments, validated_data.pop("lease_payments", None))

        return instance

    def to_representation(self, instance):

        if isinstance(instance, realty_models.Rent):
            return RentReadSerializer(
                instance
            ).data
        elif isinstance(instance, realty_models.Realty):
            return realty_serializers.RealtyBaseSerializer(
                instance
            ).data

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class ShortRentSerializer(serializers.ModelSerializer):
    """Rent Short Detail Read Serializer."""

    realty = realty_serializers.ShortRealtySerializer()

    class Meta:
        model = realty_models.Rent
        fields = ("realty",)
