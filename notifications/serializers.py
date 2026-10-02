from rest_framework import serializers

from notifications.models import DeviceToken, Notification, NotificationTemplate
from realty.models import Realty
from realty.utils import get_apartment_short_info


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор шаблонов уведомлений.
    Используется внутри NotificationSerializer."""

    class Meta:
        model = NotificationTemplate
        fields = [
            'part1',
            'part2',
        ]


class RealtyForNotificationSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Используется внутри NotificationSerializer."""

    realty_type = serializers.SlugRelatedField(
        slug_field='type',
        read_only=True,
    )
    number_of_rooms = serializers.CharField(
        source='about_apartment.number_of_rooms.number_of_rooms'
    )
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(source='about_apartment.floors_number')

    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)
    realty_status_full = serializers.CharField(
        source='realty_status.status', read_only=True
    )

    class Meta:
        model = Realty
        fields = [
            'id',
            'realty_status',
            'realty_status_full',
            'is_deleted',
            'trade_type',
            'number_of_rooms',
            'realty_type',
            'area',
            'floor',
            'floors_number',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор уведомления."""

    realty = RealtyForNotificationSerializer()

    template = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'created_at',
            'template',
            'realty',
            'is_new',
        ]

    def get_template(self, obj) -> dict[str, str | None]:
        template_data = NotificationTemplateSerializer(obj.template).data

        realty_brief_info = get_apartment_short_info(obj.realty)

        if '№___' in template_data['part1']:
            template_data['part1'] = template_data['part1'].replace(
                '№___', f'№{str(obj.realty.id)} ({realty_brief_info})'
            )

        return template_data


class IdsNotifListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников.
    Используется в множественном удалении и смене статуса"""

    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Токен устройства для пуш-уведомлений."""

    class Meta:
        model = DeviceToken
        fields = ('token', 'platform')
        extra_kwargs = {'token': {'validators': []}}
