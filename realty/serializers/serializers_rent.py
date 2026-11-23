from django.db import transaction
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
UTILITIES_REQUIRED = (
    'Укажите, включены ли коммунальные платежи: для коммерческой '
    'недвижимости это обязательное поле.'
)
COMMERCIAL_RENT_ONLY = (
    'Указывается только для аренды коммерческой недвижимости, '
    'а «{realty_type}» — жилая.'
)
COMMERCIAL_RENT_FIELDS = ('lease_type', 'utilities_included')
COMMERCIAL_RENT_REQUIRED = {
    'lease_type': LEASE_TYPE_REQUIRED,
    'utilities_included': UTILITIES_REQUIRED,
}


def is_blank(value):
    """Поле не заполнено. Отдельная проверка нужна из-за коммуналки: False —
    это ответ «не включены», а не пустое значение, поэтому обычная проверка
    на ложность тут не годится."""
    return value is None or value == ''


class RentCreateSerializer(serializers.ModelSerializer):
    """Создание аренды."""

    realty = realty_serializers.RealtyCreateSerializer(required=True)
    rental_features = specif_serializers.RentalFeaturesCreateSerializer(required=False)
    lease_payments = specif_serializers.LeasePaymentsCreateSerializer(required=False)
    utilities_included = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text='Коммунальные платежи: true — включены, false — не включены. '
        'Для коммерческой аренды обязательно, у жилой не указывается.',
    )

    def _current(self, data, field):
        """Значение поля после правки: из запроса или из того, что уже лежит."""
        return data.get(field, getattr(self.instance, field, None))

    def _kind_is_set_now(self, realty_data):
        """Вид недвижимости задаётся прямо сейчас: объявление создаётся или
        меняет тип. Тогда условия аренды проверяются целиком. Правка старой
        записи, которую вид не трогает, проверяется только по присланным
        полям — иначе объявление, заведённое до этих правил, стало бы
        нередактируемым."""
        if self.instance is None:
            return True
        return (
            'realty_type' in realty_data
            and realty_data['realty_type'] != self.instance.realty.realty_type
        )

    def validate(self, data):
        """Тип аренды и коммуналка — обязательные поля коммерческой аренды.
        У жилой аренды их наоборот не бывает."""
        realty_data = data.get('realty') or {}
        realty_type = realty_data.get('realty_type') or (
            self.instance.realty.realty_type if self.instance else None
        )
        if realty_type is None:
            return data

        kind_is_set_now = self._kind_is_set_now(realty_data)

        if realty_type.is_commercial:
            errors = {
                field: message
                for field, message in COMMERCIAL_RENT_REQUIRED.items()
                if is_blank(self._current(data, field))
                and (kind_is_set_now or field in data)
            }
        else:
            errors = {
                field: COMMERCIAL_RENT_ONLY.format(realty_type=realty_type.type)
                for field in COMMERCIAL_RENT_FIELDS
                if not is_blank(self._current(data, field))
                and (kind_is_set_now or field in data)
            }

        if errors:
            raise serializers.ValidationError(errors)
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Объявление и аренда создаются вместе: если что-то не сложилось,
        в базе не остаётся объявления без сделки."""
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

    @transaction.atomic
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
