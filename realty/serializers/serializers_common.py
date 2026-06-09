# realty/serializers/serializers_common.py

from django.core.exceptions import ValidationError
from rest_framework import serializers

from realty import models as realty_models
from realty.models import Realty
from realty.serializers import serializers_realty as realty_serializers
from realty_displays import serializers as displays_serializers
from users.serializers import UserContactsSerializer, UserDataSerializer


class CountRealtySerializer(realty_serializers.RealtyBaseSerializer):
    """Filtered Realty Count Serializer."""

    count = serializers.IntegerField()

    class Meta:
        model = realty_models.Realty
        fields = ('count',)


class RealtyOwnerDataSerializer(serializers.ModelSerializer):
    """Realty's Owner Contacts Serializer."""

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
    """Realty's Owner Contacts Serializer."""

    owner = UserContactsSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')

    class Meta:
        model = realty_models.Realty
        fields = (
            'owner',
            'owner_type',
        )


class RealtyLKSerializer(serializers.ModelSerializer):
    """Сериализатор для объектов недвижимости с добавлением счетчиков просмотров и статуса."""

    short_realty_data = realty_serializers.ShortRealtySerializer(read_only=True)
    counter_views = displays_serializers.CounterViewsSerializer(read_only=True)
    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)

    # Добавляем поля типа недвижимости
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
        # Базовое представление
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

        # статусы из realty_values_realtyadvstatus
        # 1 - Активно
        # 2 - На модерации
        # 3 - Отклонено
        # 4 - В архиве

        if instance.realty_status_id == 1:
            representation['counter_views'] = (
                displays_serializers.CounterViewsSerializer(instance).data
            )
        else:
            representation['counter_views'] = {}

        return representation


class RealtyStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for update realty_status"""

    class Meta:
        model = realty_models.Realty
        fields = ['realty_status']

    def validate_realty_status(self, value):
        obj = self.instance
        request = self.context.get('request')
        if obj.owner == request.user:
            allowed_transitions = {
                'Активно': ['В архиве'],
                'Отклонено': ['В архиве'],
                'На модерации': ['В архиве'],
                'В архиве': ['На модерации'],
            }

            if obj.realty_status.status in allowed_transitions:
                if str(value) not in allowed_transitions[obj.realty_status.status]:
                    raise ValidationError(
                        f"Статус можно изменить с '{obj.realty_status.status}' "
                        f'только на {allowed_transitions[obj.realty_status.status]}.'
                    )
            else:
                raise ValidationError(
                    f"Недопустимая операция: статус '{obj.realty_status.status}' нельзя изменить."
                )

            return value
        else:
            raise ValidationError('Вы не являетесь владельцем объявления!')
