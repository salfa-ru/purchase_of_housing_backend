from django.core.exceptions import ValidationError
from rest_framework import serializers

from config import constants
from realty import models as realty_models
from realty.models import Realty
from realty.serializers import serializers_realty as realty_serializers
from realty_displays import serializers as displays_serializers
from users.serializers import UserContactsSerializer, UserDataSerializer


class CountRealtySerializer(realty_serializers.RealtyBaseSerializer):
    """Количество объявлений после фильтров."""

    count = serializers.IntegerField()

    class Meta:
        model = realty_models.Realty
        fields = ('count',)


class RealtyOwnerDataSerializer(serializers.ModelSerializer):
    """Данные владельца объявления."""

    owner = UserDataSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')
    communication_method = serializers.CharField(
        source='communication_method.method', read_only=True
    )

    class Meta:
        model = realty_models.Realty
        fields = (
            'owner',
            'owner_type',
            'communication_method',
        )


class RealtyOwnerContactsSerializer(serializers.ModelSerializer):
    """Контакты владельца объявления."""

    owner = UserContactsSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')

    class Meta:
        model = realty_models.Realty
        fields = (
            'owner',
            'owner_type',
        )


class RealtyLKSerializer(serializers.ModelSerializer):
    """Сериализатор для объектов недвижимости с добавлением счетчиков просмотров и
    статуса.
    """

    short_realty_data = realty_serializers.ShortRealtySerializer(read_only=True)
    counter_views = displays_serializers.CounterViewsSerializer(read_only=True)
    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)

    realty_type = serializers.CharField(source='realty_type.type', read_only=True)
    is_commercial = serializers.BooleanField(
        source='realty_type.is_commercial', read_only=True
    )

    class Meta:
        model = Realty
        fields = [
            'short_realty_data',
            'realty_status',
            'counter_views',
            'realty_type',
            'is_commercial',
        ]

    def to_representation(self, instance):
        representation = {
            'short_realty_data': realty_serializers.ShortRealtySerializer(
                instance, context=self.context
            ).data,
            'realty_status': instance.realty_status_id,
            'realty_type': instance.realty_type.type if instance.realty_type else None,
            'is_commercial': instance.realty_type.is_commercial
            if instance.realty_type
            else False,
        }

        if instance.realty_status_id == constants.STATUS_ACTIVE_ID:
            representation['counter_views'] = (
                displays_serializers.CounterViewsSerializer(instance).data
            )
        else:
            representation['counter_views'] = {}

        return representation


ALLOWED_TRANSITIONS = {
    'Активно': ['В архиве'],
    'Отклонено': ['В архиве'],
    'На модерации': ['В архиве'],
    'В архиве': ['На модерации'],
}


class RealtyStatusUpdateSerializer(serializers.ModelSerializer):
    """Смена статуса объявления."""

    class Meta:
        model = realty_models.Realty
        fields = ['realty_status']

    def validate_realty_status(self, value):
        """Владельца проверяет разрешение вьюхи, здесь — только переход статуса."""
        obj = self.instance
        current = obj.realty_status.status

        if current not in ALLOWED_TRANSITIONS:
            raise ValidationError(
                f"Недопустимая операция: статус '{current}' нельзя изменить."
            )

        if str(value) not in ALLOWED_TRANSITIONS[current]:
            raise ValidationError(
                f"Статус можно изменить с '{current}' "
                f'только на {ALLOWED_TRANSITIONS[current]}.'
            )

        return value
