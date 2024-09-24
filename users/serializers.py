from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from config.constants import IMAGE_EXTENSIONS
from users.models import User, validate_avatar_size


class UserBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для профиля (retrieve, put, patch)."""
    avatar = serializers.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size
        ]
    )

    def to_internal_value(self, data):
        if data.get('email'):
            _mutable = data._mutable
            data._mutable = True
            data['email'] = data.get('email').lower()
            data._mutable = _mutable
        return super().to_internal_value(data)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'avatar',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }


class UserSelfProfileSerializer(UserBaseSerializer):
    """Используется для полного обновления профиля,
     для 'своих' пользователей."""

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + [
            'password',
        ]
        extra_kwargs_add = {
            'password': {'write_only': True},
        }
        extra_kwargs = {**UserBaseSerializer.Meta.extra_kwargs,
                        **extra_kwargs_add}


class UserFullSerializer(UserSelfProfileSerializer):
    """Сериализатор для list, create, delete.
    Полные данные по пользователю."""

    class Meta(UserSelfProfileSerializer.Meta):
        fields = UserSelfProfileSerializer.Meta.fields + [
            'phone_qr_code',
            'username',
            'user_type',
            'uuid_esa',
            'updated_at',
            'date_joined',
        ]
        extra_kwargs_add = {
            'username': {'read_only': True},
            'user_type': {'read_only': True},
            'avatar': {'read_only': True},
            'uuid_esa': {'read_only': True},
            'updated_at': {'read_only': True},
            'date_joined': {'read_only': True},
            'phone_qr_code': {'read_only': True},
        }
        extra_kwargs = {**UserSelfProfileSerializer.Meta.extra_kwargs,
                        **extra_kwargs_add}


class UserESAProfileSerializer(UserBaseSerializer):
    """Используется для частичного обновления профиля,
     для пользователей из ЕСА."""

    class Meta(UserBaseSerializer.Meta):
        extra_kwargs_add = {
            'first_name': {'read_only': True},
            'last_name': {'read_only': True},
            'email': {'read_only': True},
            'phone_number': {'read_only': True},
        }
        extra_kwargs = {**UserBaseSerializer.Meta.extra_kwargs,
                        **extra_kwargs_add}


class UserPersonalAccountSerializer(serializers.ModelSerializer):
    """Краткая информацию по пользователю. Используется в ЛК."""

    new_chats_count = serializers.SerializerMethodField()
    new_notifications_count = serializers.SerializerMethodField()

    def get_new_chats_count(self, instance):
        return instance.chats_to_me.filter(is_new=True).count()

    def get_new_notifications_count(self, instance):
        return instance.notifications.filter(is_new=True).count()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'avatar',
            'new_chats_count',
            'new_notifications_count',
        ]


class UserNewMsgsSerializer(serializers.ModelSerializer):
    """Краткая информацию по пользователю. Используется в ЛК."""

    have_new_msgs = serializers.SerializerMethodField()

    def get_have_new_msgs(self, instance) -> bool:
        return bool(
            instance.chats_to_me.filter(is_new=True).count() +
            instance.notifications.filter(is_new=True).count()
        )

    class Meta:
        model = User
        fields = [
            'id',
            'have_new_msgs',
        ]
