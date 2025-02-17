from django.db.models import Q
from rest_framework import serializers

from rest_framework import fields

from chats.models import Message, Blocking, Chat
from realty.models import Realty
from users.models import User


class ChatIdSerializer(serializers.Serializer):
    """Сериализатор для передачи chat_id в теле запроса"""
    chat_id = serializers.IntegerField(min_value=1)


class RealtyIdSerializer(serializers.Serializer):
    """Сериализатор для передачи realty_id в теле запроса"""
    realty_id = serializers.IntegerField(min_value=1)


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
            raise serializers.ValidationError(detail=
                "Должен быть передан либо chat_id, либо realty_id"
            )
        return data


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
    name = serializers.CharField(source='first_name')

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
    """Сериализатор для отображения чата с сообщениями - в краткой или в полной форме!"""
    me = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_is_owner = serializers.SerializerMethodField()
    realty = RealtyForZhatSerializer()
    messages = serializers.SerializerMethodField()
    is_blocked_i_block_them = serializers.SerializerMethodField()
    is_blocked_they_block_me = serializers.SerializerMethodField()

    # Fields for flattened last message info
    message = serializers.CharField(read_only=True, required=False)
    direction = serializers.CharField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    is_new = serializers.BooleanField(read_only=True, required=False)

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
            'messages',  # останется либо список, либо одно сообщение <-----
            'message',
            'direction',
            'created_at',
            'is_new'
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
                data['message'] = last_message.message
                data['direction'] = "in" if last_message.user_to == current_user else "out"

                # data['created_at'] = last_message.created_at
                # Use DRF's DateTimeField to format the date.
                date_field = fields.DateTimeField()
                data['created_at'] = date_field.to_representation(last_message.created_at)

                data['is_new'] = last_message.is_new if last_message.user_to == current_user else False
        else:
            # Remove the flattened fields for other endpoints
            data.pop('message', None)
            data.pop('direction', None)
            data.pop('created_at', None)
            data.pop('is_new', None)

        return data

    def get_me(self, obj):
        current_user = self.context['request'].user
        return UserInfoSerializer(current_user).data

    def get_user(self, obj):
        current_user = self.context['request'].user
        other_user = obj.owner if current_user == obj.client else obj.client
        return UserInfoSerializer(other_user).data

    def get_user_is_owner(self, obj):
        current_user = self.context['request'].user
        return current_user != obj.owner

    def get_messages(self, obj):
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

        # # Mark unread messages as read
        # messages.filter(user_to=current_user, is_new=True).update(is_new=False)
        #
        # return MessageSerializer(messages, many=True, context=self.context).data

        ''' Важное исправление - сначала показываем, что сообщения новые 
        и только делаем прочитанными (все равно будучи не уверенными, что пользователь их прочитает) '''
        # Serialize the messages *before* marking them as read.
        serialized_messages = MessageSerializer(messages, many=True, context=self.context).data

        # *Now* mark unread messages as read, after serialization.
        unread_message_ids = messages.filter(user_to=current_user, is_new=True).values_list('msg_id', flat=True)
        Message.objects.filter(msg_id__in=unread_message_ids).update(is_new=False)

        return serialized_messages


    def get_is_blocked_i_block_them(self, obj):
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=current_user,
            user_whom=other_user
        ).exists()

    def get_is_blocked_they_block_me(self, obj):
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=other_user,
            user_whom=current_user
        ).exists()

'''
# class MassageSerializer(serializers.ModelSerializer):
#     """Сериализатор одного сообщения внутри цепочки сообщений."""
#
#     class Meta:
#         model = Message
#         fields = [
#             'msg_id',
#             'message',
#             'created_at',
#             'user_from',
#             'user_to'
#         ]
'''


# class CreateMessageResponseSerializer(serializers.ModelSerializer):
#     """Сериализатор тела ответа при создании нового сообщения"""
#     class Meta:
#         model = Message
#         fields = [
#             'msg_id',
#             'message',
#             'user_from',
#             'user_to',
#             'created_at',
#             'is_deleted_from',
#             'is_deleted_to',
#         ]


class CreateMessageResponseSerializer(serializers.ModelSerializer):
    """Сериализатор тела ответа при создании нового сообщения"""
    chat_id = serializers.IntegerField(source='chat.chat_id')
    realty = RealtyNestedIdSerializer(source='chat.realty')  # Nested, only ID
    me = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_is_owner = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    is_new = serializers.BooleanField(read_only=True, required=False)

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
            # 'user_from',
            # 'user_to',

            # 'is_deleted_from',
            # 'is_deleted_to',
        ]

    def get_me(self, obj):
        return UserInfoSerializer(obj.user_from).data

    def get_user(self, obj):
        return UserInfoSerializer(obj.user_to).data

    def get_user_is_owner(self, obj):
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


class UnblockingSerializer(serializers.Serializer):
    """Сериализатор разблокировки"""
    chat_ids = serializers.ListField(  # Переименовано с 'ids' на 'chat_ids'
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Список ID чатов"
    )
