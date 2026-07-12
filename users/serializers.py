from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from config.constants import IMAGE_EXTENSIONS
from users.models import User, validate_avatar_size
from users.validators import validate_person_name, validate_phone_number


class UserBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для профиля (retrieve, put, patch)."""

    avatar = serializers.ImageField(
        required=False,
        # если нужно иметь возможность удалить аватар, добавить allow_null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size,
        ],
    )

    def to_internal_value(self, data):
        # Проверяем, что data - это словарь и что ключ 'email' присутствует и имеет значение
        if isinstance(data, dict) and 'email' in data and data['email']:
            # Приводим email к нижнему регистру
            data['email'] = data['email'].lower()
            # Вызываем родительский метод с измененными данными
            return super().to_internal_value(data)

        # Если условие не выполнено, вызываем родительский метод с исходными данными
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

    def validate(
        self, data
    ):  # <---xxx--- Добавляем валидацию на уникальность email и phone number
        """
        Проверяет, что email и phone_number не принадлежат удаленным пользователям.
        """
        email = data.get('email', getattr(self.instance, 'email', None))
        phone_number = data.get(
            'phone_number', getattr(self.instance, 'phone_number', None)
        )

        if email:
            existing_user_email = User.objects.filter(
                email=email, is_deleted=True
            ).first()
            if existing_user_email and (
                not self.instance or self.instance != existing_user_email
            ):
                raise ValidationError(
                    'Пользователь с таким адресом электронной почты уже существует и удален, обратитесь в поддержку для восстановления аккаунта или введите другой имейл.'
                )

        if phone_number:
            existing_user_phone = User.objects.filter(
                phone_number=phone_number, is_deleted=True
            ).first()
            if existing_user_phone and (
                not self.instance or self.instance != existing_user_phone
            ):
                raise ValidationError(
                    'Пользователь с таким номером телефона уже существует и удален, обратитесь в поддержку для восстановления аккаунта или введите другой номер телефона.'
                )

        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя.
    Используется в публичном API для обычных пользователей.

    Разрешённые поля:
    - first_name (имя)
    - last_name (фамилия)
    - avatar (аватарка)

    Служебные поля (is_deleted, is_active, is_staff, is_superuser, id)
    НЕДОСТУПНЫ для изменения через этот сериализатор.
    """

    # Явно переопределяем поля без валидаторов модели,
    # чтобы обычный пользователь мог обновлять профиль без ограничений
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=40)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=40)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']

    def validate_first_name(self, value):
        """Дополнительная валидация для имени (если нужна)."""
        # Здесь можно добавить бизнес-логику, если потребуется
        return value

    def validate_last_name(self, value):
        """Дополнительная валидация для фамилии (если нужна)."""
        return value

    def validate(self, attrs):
        """
        Общая валидация для всех полей.
        Можно добавить проверки, требующие нескольких полей.
        """
        # Если нужно добавить логику, например:
        # if attrs.get('first_name') and attrs.get('last_name'):
        #     # какая-то проверка
        return attrs


class AdminUserUpdateSerializer(UserBaseSerializer):
    """
    Сериализатор для администратора.
    Позволяет изменять служебные поля.
    """

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ['is_active', 'is_staff']


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

    first_name = serializers.CharField(
        required=True, allow_blank=False, validators=[validate_person_name]
    )
    last_name = serializers.CharField(
        required=True, allow_blank=False, validators=[validate_person_name]
    )

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
        extra_kwargs = {
            **UserSelfProfileSerializer.Meta.extra_kwargs,
            **extra_kwargs_add,
        }


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


class UserPersonalAccountSerializer(serializers.ModelSerializer):
    """Краткая информацию по пользователю. Используется в ЛК."""

    new_messages_count = serializers.SerializerMethodField()
    new_notifications_count = serializers.SerializerMethodField()

    def get_new_messages_count(self, instance) -> int:
        return instance.messages_received.filter(is_new=True).count()

    def get_new_notifications_count(self, instance) -> int:
        return instance.notifications.filter(is_new=True).count()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'avatar',
            'new_messages_count',
            'new_notifications_count',
        ]


class UserNewMsgsSerializer(serializers.ModelSerializer):
    """Краткая информацию по пользователю. Используется в ЛК."""

    have_new_msgs = serializers.SerializerMethodField()

    def get_have_new_msgs(self, instance) -> bool:
        return bool(
            instance.messages_received.filter(is_new=True).count()
            + instance.notifications.filter(is_new=True).count()
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
        fields = (
            'id',
            'first_name',
            'last_name',
            'registered_for',
            'avatar',
            'phone_number',
            'phone_qr_code',
        )

    def get_registered_for(self, obj) -> str:
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
        fields = ('id', 'phone_number', 'first_name', 'phone_qr_code')


# ========== СМЕНА НОМЕРА ТЕЛЕФОНА ==========
class ChangePhoneSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(
        max_length=20, validators=[validate_phone_number]
    )

    def validate_new_phone_number(self, value):
        from users.models import User

        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Этот номер телефона уже используется.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.phone_number = self.validated_data['new_phone_number']
        user.save()
        return user


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Пример регистрации',
            value={
                'username': 'user123',
                'password': 'securepass123',
                're_password': 'securepass123',
                'email': 'user@example.com',
                'phone_number': '+79991234567',
                'first_name': 'Иван',
                'last_name': 'Петров',
            },
            request_only=True,
        ),
    ]
)
class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор для регистрации нового пользователя."""

    phone_number = serializers.CharField(
        required=True, validators=[validate_phone_number]
    )
    first_name = serializers.CharField(
        required=True, allow_blank=False, validators=[validate_person_name]
    )
    last_name = serializers.CharField(
        required=True, allow_blank=False, validators=[validate_person_name]
    )
    email = serializers.EmailField(required=True)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'password',
            'email',
            'phone_number',
            'first_name',
            'last_name',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'phone_number': {'required': True},
        }
