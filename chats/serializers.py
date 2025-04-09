# chats/serializers.py

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers, fields
from rest_framework.exceptions import APIException
from rest_framework import status

from chats.models import Message, Blocking, Chat
from realty.models import Realty
from users.models import User


class RealtyNestedIdSerializer(serializers.ModelSerializer):
    """Serializer for just the Realty ID."""
    class Meta:
        model = Realty
        fields = ['id']


class CreateMessageRequestSerializer(serializers.Serializer):
    """Сериализатор для создания нового сообщения"""
    chat_id = serializers.IntegerField(min_value=1, required=False)
    realty_id = serializers.IntegerField(min_value=1, required=False)
    message = serializers.CharField(max_length=255)

    def validate(self, data):
        """Проверяем, что передан либо chat_id, либо realty_id, но не оба"""
        if ('chat_id' not in data and 'realty_id' not in data) or \
           ('chat_id' in data and 'realty_id' in data):

            raise ValidationCustomDetailError(detail="Должен быть передан либо chat_id, либо realty_id")

        return data


class RealtyForChatSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Для показа переписок и цепочек сообщений."""

    # realty_status = serializers.SlugRelatedField(
    #     slug_field='status',
    #     # <-- STATUS -- Указываем, какое поле из связанной модели RealtyAdvStatus использовать (это имя статуса)
    #     source='realty_status',  # <-- STATUS -- Указываем, какое поле в модели Realty ссылается на RealtyAdvStatus
    #     read_only=True,  # <-- STATUS -- Делаем поле только для чтения
    # )

    realty_status = serializers.SerializerMethodField()

    # owner = serializers.CharField(source='owner.username')
    owner = serializers.SerializerMethodField()  # <-- YYY --- Меняем на SerializerMethodField
    photo = serializers.SerializerMethodField()
    realty_type = serializers.SlugRelatedField(
        slug_field='type',
        read_only=True,
    )
    number_of_rooms = serializers.CharField(source='about_apartment.number_of_rooms.number_of_rooms')
    area = serializers.FloatField(source='about_apartment.area')
    floor = serializers.IntegerField(source='about_apartment.floor')
    floors_number = serializers.IntegerField(source='about_apartment.floors_number')

    def get_realty_status(self, obj):
        return obj.realty_status.status

    def get_owner(self, obj):  # <-- YYY --- Добавляем метод get_owner
        """Отображаем владельца в зависимости от его статуса."""
        if obj.owner.is_active:  # <-- YYY --- Проверяем is_active, а не is_deleted
            return obj.owner.first_name  # <-- YYY --- Возвращаем username, если владелец активен
        else:
            return "Пользователь удален"  # <-- YYY --- Возвращаем строку, если владелец удален

    def get_photo(self, obj) -> str | None:
        photo = obj.realty_photos.first()
        if photo:
            return photo.image.url
        return None

    def to_representation(self, instance):
        """Переопределяем метод to_representation."""
        if instance.is_deleted:  # <-- YYY --- Если объявление удалено
            return {
                'id': instance.id,
                'is_deleted': instance.is_deleted,
                'owner': self.get_owner(instance)
            }
        else:
            # Если объявление не удалено, возвращаем стандартное представление
            return super().to_representation(instance)

    class Meta:
        model = Realty
        fields = [
            'id',
            'is_deleted',
            'realty_status',
            'owner',
            'photo',
            'number_of_rooms',
            'realty_type',
            'area',
            'floor',
            'floors_number',
            'price',
        ]


# class UserInfoSerializer(serializers.ModelSerializer):
#     """Сериализатор для краткой информации о пользователе"""
#     name = serializers.CharField(source='username')
#
#     class Meta:
#         model = User
#         fields = ['id', 'name']


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о пользователе"""

    name = serializers.SerializerMethodField()  # Используем SerializerMethodField

    class Meta:
        model = User
        fields = ['id', 'name', 'is_deleted']

    # FIXME - Отдавать не email а имя!

    def get_name(self, obj):
        """ Если is_deleted=True - возвращает username с добавкой (Пользователь удален) ."""
        if obj.is_deleted:
            return f"Заготовка - пользователь удален ({obj.first_name})"
        return obj.first_name


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри чата"""
    direction = serializers.SerializerMethodField()
    read_at = serializers.DateTimeField(read_only=True, required=False)  # Add read_at

    class Meta:
        model = Message
        fields = [
            'msg_id',
            'message',
            'created_at',
            'direction',  # in / out
            'is_new',     # для получателя
            'read_at',    # получателем

        ]

    def get_direction(self, obj) -> str:
        current_user = self.context['request'].user
        return "in" if obj.user_to == current_user else "out"


class ChatMessagesSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения чата с сообщениями - в краткой или в полной форме!"""
    me = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_is_owner = serializers.SerializerMethodField()
    realty = RealtyForChatSerializer()
    messages = serializers.SerializerMethodField()
    i_block = serializers.SerializerMethodField()
    i_am_blocked = serializers.SerializerMethodField()

    unread = serializers.SerializerMethodField()  # Добавляем новое поле

    # Fields for flattened last message info
    message = serializers.CharField(read_only=True, required=False)
    msg_id = serializers.IntegerField(read_only=True, required=False)
    direction = serializers.CharField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    is_new = serializers.BooleanField(read_only=True, required=False)
    read_at = serializers.DateTimeField(read_only=True, required=False)  # Add read_at

    class Meta:
        model = Chat
        fields = [
            'chat_id',
            'me',
            'user',
            'user_is_owner',
            'realty',
            'i_block',
            'i_am_blocked',
            'messages',  # останется либо список, либо одно сообщение <-----
            'msg_id',
            'message',
            'direction',
            'created_at',
            'is_new',
            'read_at',  # Add read at

            'unread'  # Добавляем новое поле
        ]

    def to_representation(self, instance):
        """Override to_representation to conditionally include fields based on endpoint"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Check if we're in /chats/ or /chats/blacklist/
        if request and (request.path == '/chats/' or request.path == '/chats/blacklist/'):
            # Remove the messages list
            data.pop('messages', None)

            # Get the last message for this chat
            current_user = request.user
            last_message = instance.messages.filter(
                Q(user_from=current_user, is_deleted_from=False) |
                Q(user_to=current_user, is_deleted_to=False)
            ).order_by('-created_at').first()

            if last_message:
                # Add flattened last message info
                data['msg_id'] = last_message.msg_id
                data['message'] = last_message.message
                data['direction'] = "in" if last_message.user_to == current_user else "out"

                # data['created_at'] = last_message.created_at
                # Use DRF's DateTimeField to format the date.
                date_field = fields.DateTimeField()
                data['created_at'] = date_field.to_representation(last_message.created_at)
                data['read_at'] = date_field.to_representation(last_message.read_at)  # Add read_at

                data['is_new'] = last_message.is_new if last_message.user_to == current_user else False
        else:
            # Remove the flattened fields for other endpoints
            data.pop('msg_id', None)
            data.pop('message', None)
            data.pop('direction', None)
            data.pop('created_at', None)
            data.pop('is_new', None)
            data.pop('read_at', None)  # Remove read_at

            data.pop('unread', None)  # UNREAD IN THREAD

        return data

    def get_unread(self, obj) -> int | None:  # <------- Corrected type hint
        """Считаем количество непрочитанных сообщений в чате."""
        request = self.context.get('request')
        if request and (request.path == '/chats/' or request.path == '/chats/blacklist/'):
            current_user = request.user
            return obj.messages.filter(
                user_to=current_user,
                is_new=True,
                is_deleted_to=False
            ).count()
        return None

    @extend_schema_field(UserInfoSerializer)  # <--- Use the decorator here!
    def get_me(self, obj) -> dict:  # Type hint: Returns a dictionary
        current_user = self.context['request'].user
        return UserInfoSerializer(current_user).data

    @extend_schema_field(UserInfoSerializer)  # <--- Use the decorator here!
    def get_user(self, obj) -> dict:  # Type hint: Returns a dictionary
        current_user = self.context['request'].user
        other_user = obj.owner if current_user == obj.client else obj.client
        return UserInfoSerializer(other_user).data

    def get_user_is_owner(self, obj) -> bool:
        current_user = self.context['request'].user
        return current_user != obj.owner

    def get_messages(self, obj) -> list:
        """Get messages only for non-list endpoints"""
        request = self.context.get('request')

        # If we're in /chats/ or /chats/blacklist/, return empty list
        if request and (request.path == '/chats/' or request.path == '/chats/blacklist/'):
            return []

        current_user = self.context['request'].user
        messages = obj.messages.filter(
            Q(user_from=current_user, is_deleted_from=False) |
            Q(user_to=current_user, is_deleted_to=False)
        ).order_by('-created_at')  # <--- СОРТИРОВКА СООБЩЕНИЙ.  Newest first  <---

        """ Важное исправление - сначала показываем, что сообщения новые 
        и только делаем прочитанными (все равно будучи не уверенными, что пользователь их прочитает) """

        # TODO - ПРОВЕРИТЬ - Установка даты чтения сообщения получателем (место 2 из 2)
        print("ПРОВЕРИТЬ - Установка даты чтения сообщения получателем (место 2 из 2)!")

        # Serialize the messages *before* marking them as read.
        serialized_messages = MessageSerializer(messages, many=True, context=self.context).data

        # *Now* mark unread messages as read, after serialization.
        unread_message_ids = messages.filter(user_to=current_user, is_new=True).values_list('msg_id', flat=True)
        Message.objects.filter(msg_id__in=unread_message_ids).update(
            is_new=False,
            read_at=timezone.now()  # Add this line to set read_at timestamp
        )

        return serialized_messages

    ...

    def get_i_block(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=current_user,
            user_whom=other_user
        ).exists()

    def get_i_am_blocked(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=other_user,
            user_whom=current_user
        ).exists()


class CreateMessageResponseSerializer(serializers.ModelSerializer):
    """Сериализатор тела ответа при создании нового сообщения"""
    chat_id = serializers.IntegerField(source='chat.chat_id')
    realty = RealtyNestedIdSerializer(source='chat.realty')  # Nested, only ID
    # me = serializers.SerializerMethodField()
    # user = serializers.SerializerMethodField()
    me = UserInfoSerializer(source='user_from', read_only=True)
    user = UserInfoSerializer(source='user_to', read_only=True)
    user_is_owner = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    is_new = serializers.BooleanField(read_only=True, required=False)
    read_at = serializers.DateTimeField(read_only=True, required=False)  # Add read at - но вообще-то не нужно

    class Meta:
        model = Message
        fields = [
            'chat_id',
            'realty',
            'me',
            'user',
            'user_is_owner',
            'msg_id',
            'message',
            'created_at',
            'direction',
            'is_new',
            'read_at',  # Add read at - но вообще-то не нужно
            # 'user_from',
            # 'user_to',

            # 'is_deleted_from',
            # 'is_deleted_to',
        ]

    # def get_me(self, obj) -> dict:  # Type hint: Returns a dictionary
    #     return UserInfoSerializer(obj.user_from).data
    #
    # def get_user(self, obj) -> dict:  # Type hint: Returns a dictionary
    #     return UserInfoSerializer(obj.user_to).data

    def get_user_is_owner(self, obj) -> bool:
        return obj.user_from == obj.chat.owner

    def get_direction(self, obj) -> str:
        current_user = self.context['request'].user
        return "in" if obj.user_to == current_user else "out"


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


""" Новая сложная блокировка / разблокировка по любому параметру """


# region  Блокировка

class UserInfoIdNameSerializer(serializers.Serializer):
    """Serializer for user ID and name."""
    id = serializers.IntegerField()
    name = serializers.CharField(source='username')


class BlockingRequestSerializer(serializers.Serializer):
    """Serializer for blocking requests."""
    chat_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of Chat IDs"
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of User IDs"
    )
    realty_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of Realty IDs"
    )

    def validate(self, data):
        """Ensure only one of chat_ids, user_ids, or realty_ids is provided."""
        fields2 = ['chat_ids', 'user_ids', 'realty_ids']
        provided_fields = [field for field in fields2 if data.get(field)]

        if len(provided_fields) != 1:
            raise ValidationCustomDetailError(
                detail="Provide exactly one of: chat_ids, user_ids, or realty_ids."
            )

        return data


class ValidationCustomDetailError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation error"
    default_code = 'invalid'


class UnblockingRequestSerializer(serializers.Serializer):
    """Serializer for unblocking requests (same structure as blocking)."""
    chat_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of Chat IDs"
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of User IDs"
    )
    realty_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="List of Realty IDs"
    )

    def validate(self, data):
        """Ensure only one of chat_ids, user_ids, or realty_ids is provided."""
        fields2 = ['chat_ids', 'user_ids', 'realty_ids']
        provided_fields = [field for field in fields2 if data.get(field)]

        if len(provided_fields) != 1:
            raise ValidationCustomDetailError(
                detail="Provide exactly one of: chat_ids, user_ids, or realty_ids."
            )
        return data


class BlockingResponseSerializer(serializers.Serializer):
    """Serializer for the blocking/unblocking response."""
    current_user = serializers.CharField()
    blocked_users = UserInfoIdNameSerializer(many=True)
    blocked_chats = serializers.ListField(child=serializers.IntegerField())
    blocked_realties = serializers.ListField(child=serializers.IntegerField())


# endregion
