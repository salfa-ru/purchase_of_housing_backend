from rest_framework import serializers

from users.models import User


class UserBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для профиля (retrieve, put, patch)."""

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
        extra_kwargs = {**UserBaseSerializer.Meta.extra_kwargs, **extra_kwargs_add}


class UserFullSerializer(UserSelfProfileSerializer):
    """Сериализатор для list, create, delete.
    Полные данные по пользователю."""

    class Meta(UserSelfProfileSerializer.Meta):
        model = User
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
        extra_kwargs = {**UserSelfProfileSerializer.Meta.extra_kwargs, **extra_kwargs_add}


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
        extra_kwargs = {**UserBaseSerializer.Meta.extra_kwargs, **extra_kwargs_add}
