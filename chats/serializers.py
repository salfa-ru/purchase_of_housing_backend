from django.db.models import Q
from rest_framework import serializers

from chats.models import Chat, Blocking
from realty.models import Realty


class RealtyForChatSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Для показа переписок и цепочек сообщений."""
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

    def get_photo(self, obj):
        photo = obj.realty_photos.first()
        if photo:
            return photo.image.url
        return None

    class Meta:
        model = Realty
        fields = [
            'id',
            'owner',
            'photo',
            'number_of_rooms',
            'realty_type',
            'area',
            'floor',
            'floors_number',
            'price',
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


class IdSerializer(serializers.Serializer):
    """Сериализатор для передачи id в теле запроса"""
    id = serializers.IntegerField(min_value=1)


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри цепочки сообщений."""

    class Meta:
        model = Chat
        fields = [
            'id',
            'message',
            'datetime',
        ]


class MessagesListSerializer(serializers.ModelSerializer):
    """Сериализатор цепочки сообщений"""
    realty = RealtyForChatSerializer()
    is_blocked = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    def get_is_blocked(self, obj) -> bool:
        """Определяем, заблокировали ли текущего пользователя"""
        current_user, second_user, realty = self.get_chat_data(obj)
        is_blocked = Blocking.objects.filter(
            user_who=second_user,
            user_whom=current_user,
        ).exists()
        return is_blocked

    def get_messages(self, obj) -> MessageSerializer(many=True):
        """Получаем список сообщений в цепочке.
        Сравнение по текущему пользователю, собеседнику и объявлению.
        Удаленные сообщения не включаем."""
        current_user, second_user, realty = self.get_chat_data(obj)

        queryset = Chat.objects.filter(
            Q(
                user_from=current_user,
                is_deleted_from=False,
                user_to=second_user,
                realty=realty
            ) |
            Q(
                user_from=second_user,
                user_to=current_user,
                is_deleted_to=False,
                realty=realty
            )
        ).order_by('datetime').all()

        serializer = MessageSerializer(queryset, many=True)
        return serializer.data

    def get_chat_data(self, obj):
        """Получение данных по цепочке сообщений:
        текущий пользователь, собеседник, объявление"""
        current_user = getattr(self.context.get('request'), 'user', None)
        second_user = obj.user_from if obj.user_from != current_user else obj.user_to
        realty = obj.realty
        return current_user, second_user, realty

    class Meta:
        model = Chat
        fields = [
            'realty',
            'is_blocked',
            'messages',
        ]
