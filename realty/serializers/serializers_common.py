# realty/serializers/serializers_common.py

from django.core.exceptions import ValidationError
from rest_framework import serializers

from realty import models as realty_models
from realty_displays import serializers as displays_serializers
from realty.serializers import serializers_realty as realty_serializers
from users.serializers import UserDataSerializer, UserContactsSerializer


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
        source='communication_method.method', read_only=True)

    class Meta:
        model = realty_models.Realty
        fields = ("owner",
                  "owner_type",
                  "communication_method",
                  )


class RealtyOwnerContactsSerializer(serializers.ModelSerializer):
    """Realty's Owner Contacts Serializer."""

    owner = UserContactsSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')

    class Meta:
        model = realty_models.Realty
        fields = ("owner",
                  "owner_type",
                  )


class RealtyLKSerializer(serializers.Serializer):
    """Serializer for Realty objects with added view counts and status."""

    short_realty_data = realty_serializers.ShortRealtySerializer()
    counter_views = displays_serializers.CounterViewsSerializer()
    realty_status = serializers.IntegerField(source='realty_status_id')

    # Зачем здесь это вообще - ведь здесь не будут показаны удаленные
    is_deleted = serializers.BooleanField(read_only=True, source='short_realty_data.is_deleted')  # <-- YYY --- realty_удаление v1

    def to_representation(self, instance):
        representation = {
            'short_realty_data': realty_serializers.ShortRealtySerializer(instance, context=self.context).data,
            'realty_status': instance.realty_status_id,

            # Зачем здесь это вообще - ведь здесь не будут показаны удаленные
            'is_deleted': instance.is_deleted  # <-- YYY --- realty_удаление v1
        }

        # статусы из realty_values_realtyadvstatus
        # 1 - Активно
        # 2 - На модерации
        # 3 - Отклонено
        # 4 - В архиве

        if instance.realty_status_id == 1:  # Выдавать ответ только если объявление Активно
            representation['counter_views'] = displays_serializers.CounterViewsSerializer(instance).data
        else:
            representation['counter_views'] = {}  # пустой ответ если объявление не активно

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
                'В архиве': ['На модерации']
            }

            if obj.realty_status.status in allowed_transitions:

                if str(value) not in allowed_transitions[obj.realty_status.status]:
                    raise ValidationError(
                        f"Статус можно изменить с '{obj.realty_status.status}' "
                        f"только на {allowed_transitions[obj.realty_status.status]}."
                    )
            else:
                raise ValidationError(f"Недопустимая операция: статус '{obj.realty_status.status}' нельзя изменить.")

            return value
        else:
            raise ValidationError(f"Вы не являетесь владельцем объявления!")
