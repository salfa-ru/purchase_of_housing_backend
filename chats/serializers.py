from django.db.models import Q
from rest_framework import serializers, exceptions

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
    is_new = serializers.SerializerMethodField()

    def get_is_new(self, obj):
        return obj.user_to == self.context['request'].user and obj.is_new

    class Meta:
        model = Chat
        fields = [
            'id',
            'realty',
            'message',
            'datetime',
            'is_new',
            'user_from',
            'user_to',
        ]


class IdSerializer(serializers.Serializer):
    """Сериализатор для передачи id в теле запроса"""
    id_from = serializers.IntegerField(min_value=1)


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри цепочки сообщений."""

    class Meta:
        model = Chat
        fields = [
            'id',
            'message',
            'datetime',
            'user_from',
            'user_to'
        ]


class MessagesListBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор цепочки сообщений (для наследования от него)"""
    realty = None
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

        # Меняем статус "Новое", когда отдали цепочку сообщений
        queryset.filter(
            user_to=current_user, is_new=True
        ).all().update(is_new=False)

        serializer = MessageSerializer(queryset, many=True)
        return serializer.data

    def get_chat_data(self, obj):
        """Получение данных по объекту сериализатора
        (переписке или объявлению),
         будет переопределено в наследуюемых классах"""
        current_user = None
        second_user = None
        realty = None
        return current_user, second_user, realty

    class Meta:
        fields = [
            'realty',
            'is_blocked',
            'messages',
        ]


class MessagesListPASerializer(MessagesListBaseSerializer):
    """Сериализатор цепочки сообщений для личного кабинета."""

    realty = RealtyForChatSerializer()

    class Meta(MessagesListBaseSerializer.Meta):
        model = Chat

    def get_chat_data(self, obj):
        """Получение данных по сообщению (из ЛК):
        текущий пользователь, собеседник, объявление"""
        current_user = getattr(self.context.get('request'), 'user', None)
        second_user = obj.user_from if obj.user_from != current_user else obj.user_to
        realty = obj.realty
        return current_user, second_user, realty


class MessagesListRealtySerializer(MessagesListBaseSerializer):
    """Сериализатор цепочки сообщений из объявления."""

    realty = RealtyForChatSerializer(source='*')

    class Meta(MessagesListBaseSerializer.Meta):
        model = Realty

    def get_chat_data(self, obj):
        """Получение данных по объявлению:
        текущий пользователь, собеседник, объявление"""
        current_user = getattr(self.context.get('request'), 'user', None)
        second_user = obj.owner
        realty = obj
        return current_user, second_user, realty


class CreateChatRequestSerializer(serializers.Serializer):
    """Сериализатор тела запроса при создании нового сообщения"""
    id_from = serializers.IntegerField(min_value=1, write_only=True)
    message = serializers.CharField(max_length=255)


class CreateChatResponseSerializer(serializers.ModelSerializer):
    """Сериализатор тела ответа при создании нового сообщения"""

    class Meta:
        model = Chat
        fields = [
            'id',
            'message',
            'user_from',
            'user_to',
            'realty',
            'datetime',
            'is_deleted_from',
            'is_deleted_to',
        ]

    def validate(self, attrs):
        """Добавление проверки на блокировку"""
        data = super().validate(attrs)
        is_blocked = Blocking.objects.filter(
            user_who=data.get('user_to'),
            user_whom=data.get('user_from'),
        ).exists()
        if is_blocked:
            msg = "Chat blocked."
            raise exceptions.PermissionDenied(detail=msg)
        # проверка на отправку сообщения самому себе
        if data.get("user_from") == data.get("user_to"):
            raise exceptions.ValidationError("You cannot send a message to yourself.")

        return data


class IdsListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников.
    Используется в множественном удалении и блокировке"""
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True
    )


class BlockingSerializer(serializers.ModelSerializer):
    """Сериализатор блокировки чатов пользователя"""
    user_who = serializers.SlugRelatedField(read_only=True,
                                            slug_field='username')
    user_whom = serializers.SlugRelatedField(read_only=True,
                                             slug_field='username')

    class Meta:
        model = Blocking
        fields = [
            'id',
            'user_who',
            'user_whom',
        ]


class UnblockingSerializer(serializers.ModelSerializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Список ID чатов для разблокировки"
    )

    def validate_ids(self, value):
        if not Chat.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("Некоторые из переданных чатов не существуют.")
