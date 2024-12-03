from rest_framework import serializers

from notifications.models import Notification, NotificationTemplate
from realty.models import Realty


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
            'datetime',
            'template',
            'realty',
            'is_new',
        ]

    def get_template(self, obj):
        # Получаем оригинальные темплейты из стандартного сериализатора
        template_data = NotificationTemplateSerializer(obj.template).data

        # Вставляем номер объявление вместо подчеркивания - ищем его только в первой части
        if '№___' in template_data['part1']:
            template_data['part1'] = template_data['part1'].replace('№___', "№"+str(obj.realty.id))

        return template_data


class IdsListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников.
    Используется в множественном удалении и смене статуса"""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )
