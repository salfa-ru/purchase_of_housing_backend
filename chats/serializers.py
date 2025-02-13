from django.db.models import Q
from rest_framework import serializers

from chats.models import Message, Blocking, Chat
from realty.models import Realty
from users.models import User


class RealtyForZhatSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Для показа переписок и цепочек сообщений."""
    owner = serializers.CharField(source='owner.first_name')
    photo = serializers.SerializerMethodField()
    realty_type = serializers.SlugRelatedField(
        slug_field='type',
        read_only=True,
    )
    number_of_rooms = serializers.CharField(source='about_apartment.number_of_rooms.number_of_rooms')
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(source='about_apartment.floors_number')

    def get_photo(self, obj) -> str | None:
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


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о пользователе"""
    name = serializers.CharField(source='first_name')  # This is the key change

    class Meta:
        model = User
        fields = ['id', 'name']


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри чата"""
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'msg_id',
            'message',
            'created_at',
            'direction',  # True если сообщение входящее дял текущего пользователя
            'is_new'
        ]

    def get_direction(self, obj) -> str:
        current_user = self.context['request'].user
        return "in" if obj.user_to == current_user else "out"


class ChatMessagesSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения чата с сообщениями"""
    me = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_is_owner = serializers.SerializerMethodField()
    realty = RealtyForZhatSerializer()
    messages = MessageSerializer(many=True, source='messages.all')
    is_blocked_i_block_them = serializers.SerializerMethodField()
    is_blocked_they_block_me = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'chat_id',
            'me',
            'user',
            'user_is_owner',
            'realty',
            'is_blocked_i_block_them',
            'is_blocked_they_block_me',
            'messages'
        ]

    def get_me(self, obj) -> int:
        current_user = self.context['request'].user
        return UserInfoSerializer(current_user).data

    def get_user(self, obj) -> int:
        current_user = self.context['request'].user
        other_user = obj.owner if current_user == obj.client else obj.client
        return UserInfoSerializer(other_user).data

    def get_user_is_owner(self, obj) -> bool:
        current_user = self.context['request'].user
        return current_user != obj.owner

    def get_is_blocked_i_block_them(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=current_user,
            user_whom=other_user
        ).exists()

    def get_is_blocked_they_block_me(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=other_user,
            user_whom=current_user
        ).exists()


class IdSerializer(serializers.Serializer):
    """Сериализатор для передачи id в теле запроса"""
    id_from = serializers.IntegerField(min_value=1)


class MassageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри цепочки сообщений."""

    class Meta:
        model = Message
        fields = [
            'msg_id',
            'message',
            'created_at',
            'user_from',
            'user_to'
        ]


class MassagesListBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор цепочки сообщений"""
    realty = None
    is_blocked_i_block_them = serializers.SerializerMethodField()
    is_blocked_they_block_me = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    def get_is_blocked_i_block_them(self, obj) -> bool:
        """Определяем, заблокировал ли текущий пользователь другого."""
        current_user, second_user, realty = self.get_zhat_data(obj)
        is_blocked_i_block_them = Blocking.objects.filter(
            user_who=current_user,
            user_whom=second_user,
        ).exists()
        return is_blocked_i_block_them

    def get_is_blocked_they_block_me(self, obj) -> bool:
        """Определяем, заблокировал ли другой пользователь текущего."""
        current_user, second_user, realty = self.get_zhat_data(obj)
        is_blocked_they_block_me = Blocking.objects.filter(
            user_who=second_user,
            user_whom=current_user,
        ).exists()
        return is_blocked_they_block_me

    def get_messages(self, obj) -> MassageSerializer(many=True):
        """Получаем список сообщений в цепочке."""
        current_user, second_user, realty = self.get_zhat_data(obj)

        queryset = Message.objects.filter(
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
        ).order_by('created_at').all()

        # Меняем статус "Новое", когда отдали цепочку сообщений
        queryset.filter(
            user_to=current_user, is_new=True
        ).all().update(is_new=False)

        serializer = MassageSerializer(queryset, many=True)
        return serializer.data

    def get_zhat_data(self, obj):
        """Получение данных"""
        current_user = None
        second_user = None
        realty = None
        return current_user, second_user, realty

    class Meta:
        fields = [
            'realty',
            'is_blocked_i_block_them',
            'is_blocked_they_block_me',
            'messages',
        ]


# class MassagesListPASerializer(MassagesListBaseSerializer):  # Still useful for the realty-based view
#     """Сериализатор цепочки сообщений для личного кабинета."""
#
#     realty = RealtyForZhatSerializer()
#
#     class Meta(MassagesListBaseSerializer.Meta):
#         model = Message
#
#     def get_zhat_data(self, obj):
#         """Получение данных по сообщению (из ЛК):
#         текущий пользователь, собеседник, объявление"""
#         current_user = getattr(self.context.get('request'), 'user', None)
#         second_user = obj.user_from if obj.user_from != current_user else obj.user_to
#         realty = obj.realty
#         return current_user, second_user, realty


class MassagesListRealtySerializer(MassagesListBaseSerializer):
    """Сериализатор цепочки сообщений из объявления."""

    realty = RealtyForZhatSerializer(source='*')

    class Meta(MassagesListBaseSerializer.Meta):
        model = Realty

    def get_zhat_data(self, obj):
        """Получение данных по объявлению:
        текущий пользователь, собеседник, объявление"""
        current_user = getattr(self.context.get('request'), 'user', None)
        second_user = obj.owner
        realty = obj
        return current_user, second_user, realty


class CreateZhatRequestSerializer(serializers.Serializer):
    """Сериализатор тела запроса при создании нового сообщения"""
    id_from = serializers.IntegerField(min_value=1, write_only=True)  # TODO - Can be chat_id or realty_id
    message = serializers.CharField(max_length=255)


class CreateZhatResponseSerializer(serializers.ModelSerializer):
    """Сериализатор тела ответа при создании нового сообщения"""
    class Meta:
        model = Message
        fields = [
            'msg_id',
            'message',
            'user_from',
            'user_to',
            'created_at',
            'is_deleted_from',
            'is_deleted_to',
        ]



class IdsListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников чатов.
    Используется в множественном удалении и блокировке"""
    chat_ids = serializers.ListField(  # Переименовано с 'ids' на 'chat_ids'
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        help_text="Список ID чатов (chat_ids)"
    )



class BlockingSerializer(serializers.ModelSerializer):
    """Сериализатор блокировки"""
    user_who = serializers.SlugRelatedField(read_only=True, slug_field='username')
    user_whom = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = Blocking
        fields = [
            'id',
            'user_who',
            'user_whom',
        ]


# class UnblockingSerializer(serializers.ModelSerializer): # remove ModelSerializer!
class UnblockingSerializer(serializers.Serializer):
    """Сериализатор разблокировки"""
    chat_ids = serializers.ListField(  # Переименовано с 'ids' на 'chat_ids'
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Список ID чатов"
    )

    # def validate_ids(self, value): # Moved to services.py
    #     if not Message.objects.filter(id__in=value).exists():
    #         raise serializers.ValidationError("Некоторые чаты не существуют.")
