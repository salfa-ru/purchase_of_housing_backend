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
            realty_data["realty_type"] = realty_data["realty_type"].pk
            realty_data["address"]["street"]["zone"] = realty_data["address"]["street"]["zone"].pk
            realty_data["address"]["street"]["district"] = realty_data["address"]["street"]["district"].pk
            realty_data["address"]["street"]["city"] = realty_data["address"]["street"]["city"].pk
            realty_data["address"]["metro"] = realty_data["address"]["metro"].pk
            realty_data["about_building"]["type"] = realty_data["about_building"]["type"].pk
            realty_data["about_apartment"]["number_of_rooms"] = realty_data["about_apartment"]["number_of_rooms"].pk
            realty_data["common_characteristics"]["repair_type"] = realty_data["common_characteristics"][
                "repair_type"].pk
            realty_data["common_characteristics"]["bathroom"] = realty_data["common_characteristics"]["bathroom"].pk
            realty_data["owner_type"] = realty_data["owner_type"].pk
            realty_data["communication_method"] = realty_data["communication_method"].pk

            realty_serializer = realty_serializers.RealtyCreateSerializer(
                instance=instance.realty,
                data=realty_data,
                partial=True
            )
            realty_serializer.is_valid(raise_exception=True)
            realty_serializer.save()

        # Обновление поля rental_features
        if "rental_features" in validated_data:
            rental_features_data = validated_data.pop('rental_features', None)
            related_instance_rental_features = instance.rental_features

            if related_instance_rental_features:
                for attr, value in rental_features_data.items():
                    setattr(instance.rental_features, attr, value)
                related_instance_rental_features.save()

        # Обновление поля lease_payments
        if "lease_payments" in validated_data:
            lease_payments_data = validated_data.pop('lease_payments', None)
            related_instance_lease_payments = instance.lease_payments

            if related_instance_lease_payments:
                for attr, value in lease_payments_data.items():
                    setattr(related_instance_lease_payments, attr, value)
                related_instance_lease_payments.save()

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
