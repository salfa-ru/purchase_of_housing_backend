from typing import Dict, Optional

from rest_framework import serializers

from notifications.models import Notification, NotificationTemplate
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
    realty_type = serializers.SlugRelatedField(slug_field='type',
                                               read_only=True, )
    number_of_rooms = serializers.CharField(
        source='about_apartment.number_of_rooms.number_of_rooms')
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(
        source='about_apartment.floors_number')

    class Meta:
        model = Realty
        fields = [
            'id',
            'number_of_rooms',
            'realty_type',
            'area',
            'floor',
            'floors_number',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Notification base serializer"""
    realty = RealtyForNotificationSerializer()

    # оригинальный сериалайзер, выдающий текст Уведомлений без изменений типа "Ваше объявление №___ опубликовано"
    # template = NotificationTemplateSerializer()

    # метод, подставляющий номер объявления
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

    def get_template(self, obj) -> Dict[str, Optional[str]]:  # внутри output-а могут быть строки или ничего

        # Получаем оригинальные темплейты из стандартного сериализатора
        template_data = NotificationTemplateSerializer(obj.template).data

        # Get brief realty info
        realty_brief_info = get_apartment_short_info(obj.realty)

        # Вставляем номер объявление вместо подчеркивания - ищем его только в первой части
        if '№___' in template_data['part1']:
            template_data['part1'] = (template_data['part1'].
                                      replace('№___', f"№{str(obj.realty.id)} ({realty_brief_info})"))

        return template_data


class IdsNotifListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников.
    Используется в множественном удалении и смене статуса"""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )
