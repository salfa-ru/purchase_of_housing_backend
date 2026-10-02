from django.core.validators import MaxLengthValidator
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import fields, serializers, status
from rest_framework.exceptions import APIException

from chats.models import Blocking, Chat, Message
from chats.restrictions import (
    SEND_DENIED_REALTY_ARCHIVED,
    SEND_DENIED_REALTY_DELETED,
    get_send_restriction,
    is_archived,
)
from config.constants import MESSAGE_LENGTH
from realty.models import Realty
from users.models import User


class RealtyNestedIdSerializer(serializers.ModelSerializer):
    """Только id объявления."""

    class Meta:
        model = Realty
        fields = ['id']


class CreateMessageRequestSerializer(serializers.Serializer):
    """Сериализатор для создания нового сообщения"""

    chat_id = serializers.IntegerField(min_value=1, required=False)
    realty_id = serializers.IntegerField(min_value=1, required=False)
    message = serializers.CharField(
        validators=[
            MaxLengthValidator(
                MESSAGE_LENGTH,
                message='Сообщение не должно превышать %(limit_value)d '
                'символов, сейчас %(show_value)d.',
            )
        ],
    )

    def validate(self, data):
        """Проверяем, что передан либо chat_id, либо realty_id, но не оба"""
        if ('chat_id' not in data and 'realty_id' not in data) or (
            'chat_id' in data and 'realty_id' in data
        ):
            raise ValidationCustomDetailError(
                detail='Должен быть передан либо chat_id, либо realty_id'
            )

        chat_id = data.get('chat_id')
        realty_id = data.get('realty_id')

        realty = None

        if chat_id:
            try:
                chat = Chat.objects.get(pk=chat_id)
                realty = chat.realty
            except Chat.DoesNotExist as err:
                raise ValidationCustomDetailError(detail='Чат не найден') from err

        elif realty_id:
            try:
                realty = Realty.objects.get(pk=realty_id)
            except Realty.DoesNotExist as err:
                raise ValidationCustomDetailError(
                    detail='Объявление не найдено'
                ) from err

        if realty and realty.is_deleted:
            raise ValidationCustomDetailError(detail=SEND_DENIED_REALTY_DELETED)

        if realty and is_archived(realty):
            raise ValidationCustomDetailError(detail=SEND_DENIED_REALTY_ARCHIVED)

        return data


class RealtyForChatSerializer(serializers.ModelSerializer):
    """Сериализатор информации об объявлении.
    Для показа переписок и цепочек сообщений."""

    realty_status = serializers.SerializerMethodField()

    owner = serializers.SerializerMethodField()
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
    floors_number = serializers.IntegerField(source='about_apartment.floors_number')

    def get_realty_status(self, obj):
        return obj.realty_status.status

    def get_owner(self, obj):
        """Отображаем владельца в зависимости от его статуса."""
        if obj.owner.is_active:
            return obj.owner.first_name
        else:
            return 'Пользователь удален'

    def get_photo(self, obj) -> str | None:
        photo = obj.realty_photos.first()
        if photo:
            return photo.image.url
        return None

    def to_representation(self, instance):
        """Переопределяем метод to_representation."""
        if instance.is_deleted:
            return {
                'id': instance.id,
                'is_deleted': instance.is_deleted,
                'owner': self.get_owner(instance),
            }
        else:
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


class UserInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о пользователе"""

    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'is_deleted']

    def get_name(self, obj):
        """Имя пользователя; для удаленного — с пометкой об удалении."""
        if obj.is_deleted:
            return f'Пользователь удален ({obj.first_name})'
        return obj.first_name


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор одного сообщения внутри чата"""

    direction = serializers.SerializerMethodField()
    read_at = serializers.DateTimeField(read_only=True, required=False)

    class Meta:
        model = Message
        fields = [
            'msg_id',
            'message',
            'created_at',
            'direction',
            'is_new',
            'read_at',
        ]

    def get_direction(self, obj) -> str:
        current_user = self.context['request'].user
        return 'in' if obj.user_to == current_user else 'out'


class ChatMessagesSerializer(serializers.ModelSerializer):
    """Чат с сообщениями: в краткой или в полной форме."""

    me = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_is_owner = serializers.SerializerMethodField()
    realty = RealtyForChatSerializer()
    messages = serializers.SerializerMethodField()
    i_block = serializers.SerializerMethodField()
    i_am_blocked = serializers.SerializerMethodField()

    unread = serializers.SerializerMethodField()

    can_send = serializers.SerializerMethodField()
    disabled_reason = serializers.SerializerMethodField()

    message = serializers.CharField(read_only=True, required=False)
    msg_id = serializers.IntegerField(read_only=True, required=False)
    direction = serializers.CharField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    is_new = serializers.BooleanField(read_only=True, required=False)
    read_at = serializers.DateTimeField(read_only=True, required=False)

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
            'can_send',
            'disabled_reason',
            'messages',
            'msg_id',
            'message',
            'direction',
            'created_at',
            'is_new',
            'read_at',
            'unread',
        ]

    def to_representation(self, instance):
        """Набор полей зависит от режима: короткий список или полный чат."""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if self.context.get('short'):
            data.pop('messages', None)

            current_user = request.user
            last_message = (
                instance.messages.filter(
                    Q(user_from=current_user, is_deleted_from=False)
                    | Q(user_to=current_user, is_deleted_to=False)
                )
                .order_by('-created_at')
                .first()
            )

            if last_message:
                data['msg_id'] = last_message.msg_id
                data['message'] = last_message.message
                data['direction'] = (
                    'in' if last_message.user_to == current_user else 'out'
                )

                date_field = fields.DateTimeField()
                data['created_at'] = date_field.to_representation(
                    last_message.created_at
                )
                data['read_at'] = date_field.to_representation(last_message.read_at)

                data['is_new'] = (
                    last_message.is_new
                    if last_message.user_to == current_user
                    else False
                )
        else:
            data.pop('msg_id', None)
            data.pop('message', None)
            data.pop('direction', None)
            data.pop('created_at', None)
            data.pop('is_new', None)
            data.pop('read_at', None)

            data.pop('unread', None)

        return data

    def get_unread(self, obj) -> int | None:
        """Считаем количество непрочитанных сообщений в чате."""
        request = self.context.get('request')
        if self.context.get('short'):
            current_user = request.user
            return obj.messages.filter(
                user_to=current_user, is_new=True, is_deleted_to=False
            ).count()
        return None

    @extend_schema_field(UserInfoSerializer)
    def get_me(self, obj) -> dict:
        current_user = self.context['request'].user
        return UserInfoSerializer(current_user).data

    @extend_schema_field(UserInfoSerializer)
    def get_user(self, obj) -> dict:
        current_user = self.context['request'].user
        other_user = obj.owner if current_user == obj.client else obj.client
        return UserInfoSerializer(other_user).data

    def get_user_is_owner(self, obj) -> bool:
        current_user = self.context['request'].user
        return current_user != obj.owner

    def get_messages(self, obj) -> list:
        """Сообщения отдаются только там, где это не список чатов."""
        if self.context.get('short'):
            return []

        current_user = self.context['request'].user
        messages = obj.messages.filter(
            Q(user_from=current_user, is_deleted_from=False)
            | Q(user_to=current_user, is_deleted_to=False)
        ).order_by('-created_at')

        serialized_messages = MessageSerializer(
            messages, many=True, context=self.context
        ).data

        unread_message_ids = messages.filter(
            user_to=current_user, is_new=True
        ).values_list('msg_id', flat=True)
        Message.objects.filter(msg_id__in=unread_message_ids).update(
            is_new=False,
            read_at=timezone.now(),
        )

        return serialized_messages

    def get_can_send(self, obj) -> bool:
        """Можно ли писать в этот чат."""
        current_user = self.context['request'].user
        return get_send_restriction(current_user, chat=obj) is None

    def get_disabled_reason(self, obj) -> str | None:
        """Причина, по которой писать нельзя (удалённое объявление и т.д.)."""
        current_user = self.context['request'].user
        return get_send_restriction(current_user, chat=obj)

    def get_i_block(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=current_user, user_whom=other_user
        ).exists()

    def get_i_am_blocked(self, obj) -> bool:
        current_user = self.context['request'].user
        other_user = obj.client if current_user == obj.owner else obj.owner
        return Blocking.objects.filter(
            user_who=other_user, user_whom=current_user
        ).exists()


class CreateMessageResponseSerializer(serializers.ModelSerializer):
    """Сериализатор тела ответа при создании нового сообщения"""

    chat_id = serializers.IntegerField(source='chat.chat_id')
    realty = RealtyNestedIdSerializer(source='chat.realty')
    me = UserInfoSerializer(source='user_from', read_only=True)
    user = UserInfoSerializer(source='user_to', read_only=True)
    user_is_owner = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    is_new = serializers.BooleanField(read_only=True, required=False)
    read_at = serializers.DateTimeField(read_only=True, required=False)

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
            'read_at',
        ]

    def get_user_is_owner(self, obj) -> bool:
        return obj.user_from == obj.chat.owner

    def get_direction(self, obj) -> str:
        current_user = self.context['request'].user
        return 'in' if obj.user_to == current_user else 'out'


class IdsListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников чатов.
    Используется в множественном удалении и блокировке"""

    chat_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        help_text='Список ID чатов (chat_ids)',
    )


class MsgIdsListSerializer(serializers.Serializer):
    """Сериализатор списка id-шников сообщений.
    Используется в удалении сообщений"""

    msg_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        help_text='Список ID сообщений (msg_ids)',
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


class UserInfoIdNameSerializer(serializers.Serializer):
    """id и имя пользователя."""

    id = serializers.IntegerField()
    name = serializers.CharField(source='username')


class BlockingRequestSerializer(serializers.Serializer):
    """Запрос на блокировку."""

    chat_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of Chat IDs',
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of User IDs',
    )
    realty_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of Realty IDs',
    )

    def validate(self, data):
        """Передать можно только одно из полей: chat_ids, user_ids или realty_ids."""
        fields2 = ['chat_ids', 'user_ids', 'realty_ids']
        provided_fields = [field for field in fields2 if data.get(field)]

        if len(provided_fields) != 1:
            raise ValidationCustomDetailError(
                detail='Provide exactly one of: chat_ids, user_ids, or realty_ids.'
            )

        return data


class ValidationCustomDetailError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error'
    default_code = 'invalid'


class UnblockingRequestSerializer(serializers.Serializer):
    """Запрос на разблокировку: структура та же, что у блокировки."""

    chat_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of Chat IDs',
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of User IDs',
    )
    realty_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text='List of Realty IDs',
    )

    def validate(self, data):
        """Передать можно только одно из полей: chat_ids, user_ids или realty_ids."""
        fields2 = ['chat_ids', 'user_ids', 'realty_ids']
        provided_fields = [field for field in fields2 if data.get(field)]

        if len(provided_fields) != 1:
            raise ValidationCustomDetailError(
                detail='Provide exactly one of: chat_ids, user_ids, or realty_ids.'
            )
        return data


class BlockingResponseSerializer(serializers.Serializer):
    """Ответ на блокировку и разблокировку."""

    current_user = serializers.CharField()
    blocked_users = UserInfoIdNameSerializer(many=True)
    blocked_chats = serializers.ListField(child=serializers.IntegerField())
    blocked_realties = serializers.ListField(child=serializers.IntegerField())
