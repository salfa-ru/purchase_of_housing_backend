from datetime import datetime

from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from config.constants import IMAGE_EXTENSIONS
from users.models import User, validate_avatar_size


class UserBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для профиля (retrieve, put, patch)."""
    avatar = serializers.ImageField(
        required=False,
        # если нужно иметь возможность удалить аватар, добавить allow_null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size
        ]
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and data.get('email'):
            new_data = data.copy()  # Create a new dictionary
            new_data['email'] = new_data['email'].lower()
            return super().to_internal_value(new_data)
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


class UserDataSerializer(UserBaseSerializer):
    """Сериализатор для отображения данных для карточки контактов."""

    registered_for = serializers.SerializerMethodField()

    class Meta(UserBaseSerializer.Meta):
        fields = ('id',
                  'first_name',
                  'last_name',
                  'registered_for',
                  'avatar',
                  "phone_number",
                  "phone_qr_code",
                  )

    def get_registered_for(self, obj):
        now = datetime.now()
        date_joined = obj.date_joined
        years = now.year - date_joined.year
        months = now.month - date_joined.month

        if months < 0:
            years -= 1
            months += 12

        months_endings = {
            (5, 12): 'месяцев',
            (2, 4): 'месяца',
            (1, 1): 'месяц',
        }

        years_endings = {
            (5, 20): 'лет',
            (2, 4): 'года',
            (1, 1): 'год',
        }

        def get_ending(value, endings):
            """Функция для возврата правильного окончания."""
            for (start, end), ending in endings.items():
                if start <= value <= end:
                    return ending
            return list(endings.values())[-1]

        if years > 0 and months > 0:
            return f'{years} {get_ending(years, years_endings)} и {months} {get_ending(months, months_endings)} на сайте'
        elif years > 0:
            return f'{years} {get_ending(years, years_endings)} на сайте'
        elif months > 0:
            return f'{months} {get_ending(months, months_endings)} на сайте'
        else:
            return 'менее месяца на сайте'


class UserContactsSerializer(UserBaseSerializer):
    """Сериализатор для отображения карточки контактов."""

    class Meta(UserBaseSerializer.Meta):
        fields = ('id',
                  'phone_number',
                  'first_name',
                  'phone_qr_code'
                  )
