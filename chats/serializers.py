from rest_framework import serializers

from chats.models import Chat
from realty.models import Realty
from realty_photos.models import RealtyPhoto


class RealtyForChatSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Используется внутри ChatSerializer."""
    owner = serializers.CharField(source='owner.first_name')
    photo = serializers.SerializerMethodField()
    realty_type = serializers.SlugRelatedField(
        slug_field='type',
        read_only=True,
    )
    number_of_rooms = serializers.CharField(
        source='about_apartment.number_of_rooms.number_of_rooms'
    )
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(
        source='about_apartment.floors_number'
    )

    def get_photo(self, instance):
        photo = instance.realty_photos.first()
        if photo:
            return photo.image.url
        return None

    class Meta:
        model = Realty
        fields = [
            'id',
            'owner',
            'number_of_rooms',
            'realty_type',
            'area',
            'floor',
            'floors_number',
            'photo',
        ]


class ChatSerializer(serializers.ModelSerializer):
    """Сериализатор для получения списка переписок"""
    realty = RealtyForChatSerializer()

    class Meta:
        model = Chat
        fields = [
            'id',
            'realty',
            'message',
            'datetime',
            'is_new',
        ]
