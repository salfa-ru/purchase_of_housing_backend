from rest_framework import serializers

from notifications.models import Notification, NotificationTemplate
from realty.models import Realty
from realty_specificities.models import AboutApartment


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
    realty_type = serializers.SlugRelatedField(slug_field='type', read_only=True, )
    number_of_rooms = serializers.CharField(source='about_apartment.number_of_rooms.number_of_rooms')
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(source='about_apartment.floors_number')

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
    template = NotificationTemplateSerializer()
    realty = RealtyForNotificationSerializer()

    class Meta:
        model = Notification
        fields = [
            'id',
            'datetime',
            'template',
            'realty',
            'is_new',
        ]


class IdsListSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )
