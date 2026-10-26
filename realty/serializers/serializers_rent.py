from rest_framework import serializers

from realty import models as realty_models
from realty.serializers import serializers_realty as realty_serializers
from realty_specificities import models as specificities_models
from realty_specificities import serializers as specif_serializers


class RentReadSerializer(serializers.ModelSerializer):
    """Чтение аренды."""

    realty = realty_serializers.RealtyBaseSerializer()

    class Meta:
        model = realty_models.Rent
        exclude = (
            'rental_features',
            'lease_payments',
        )


LEASE_TYPE_REQUIRED = 'Тип аренды обязателен для коммерческой недвижимости.'
COMMERCIAL_RENT_ONLY = (
    'Указывается только для аренды коммерческой недвижимости, '
    'а «{realty_type}» — жилая.'
)
COMMERCIAL_RENT_FIELDS = ('lease_type', 'utilities_included')


class RentCreateSerializer(serializers.ModelSerializer):
    """Создание аренды."""

    realty = realty_serializers.RealtyCreateSerializer(required=True)
    rental_features = specif_serializers.RentalFeaturesCreateSerializer(required=False)
    lease_payments = specif_serializers.LeasePaymentsCreateSerializer(required=False)

    def validate(self, data):
        """Тип аренды и коммуналка — поля коммерческой аренды."""
        realty_data = data.get('realty') or {}
        realty_type = realty_data.get('realty_type') or (
            self.instance.realty.realty_type if self.instance else None
        )
        if realty_type is None:
            return data

        if realty_type.is_commercial:
            lease_type = data.get(
                'lease_type', self.instance.lease_type if self.instance else None
            )
            if not lease_type:
                raise serializers.ValidationError({'lease_type': LEASE_TYPE_REQUIRED})
        else:
            errors = {
                field: COMMERCIAL_RENT_ONLY.format(realty_type=realty_type.type)
                for field in COMMERCIAL_RENT_FIELDS
                if data.get(field) is not None
            }
            if errors:
                raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        realty_data = validated_data.pop('realty', None)
        rental_features_data = validated_data.pop('rental_features', None)
        lease_payments_data = validated_data.pop('lease_payments', None)

        if realty_data:
            realty_data['owner'] = self.context['request'].user
            realty = realty_serializers.RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data['realty'] = realty

        rental_features = (
            specificities_models.RentalFeatures.objects.create(**rental_features_data)
            if rental_features_data
            else None
        )
        validated_data['rental_features'] = rental_features

        lease_payments = (
            specificities_models.LeasePayments.objects.create(**lease_payments_data)
            if lease_payments_data
            else None
        )
        validated_data['lease_payments'] = lease_payments
        validated_data.pop('owner', None)
        rent = realty_models.Rent.objects.create(**validated_data)
        return rent

    def update(self, instance, validated_data):
        realty_data = validated_data.pop('realty', None)
        realty_instance = instance.realty

        if realty_data:
            realty_serializer = realty_serializers.RealtyCreateSerializer(
                context=self.context
            )
            realty_serializer._update_realty(realty_instance, realty_data)

        def update_related(instance_field, related_data):
            if instance_field and related_data:
                for attr, value in related_data.items():
                    setattr(instance_field, attr, value)
                instance_field.save()

        update_related(
            instance.rental_features, validated_data.pop('rental_features', None)
        )

        update_related(
            instance.lease_payments, validated_data.pop('lease_payments', None)
        )

        changed = [field for field in COMMERCIAL_RENT_FIELDS if field in validated_data]
        for field in changed:
            setattr(instance, field, validated_data[field])
        if changed:
            instance.save(update_fields=changed)

        return instance

    def to_representation(self, instance):
        if isinstance(instance, realty_models.Rent):
            return RentReadSerializer(instance).data
        elif isinstance(instance, realty_models.Realty):
            return realty_serializers.RealtyBaseSerializer(instance).data

    class Meta:
        model = realty_models.Rent
        fields = '__all__'
