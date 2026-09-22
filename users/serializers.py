from datetime import datetime

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from config.constants import IMAGE_EXTENSIONS
from users.models import User, validate_avatar_min_resolution, validate_avatar_size
from users.validators import (
    NAME_INVALID_CHARACTERS,
    PASSWORD_CONFIRMATION_REQUIRED,
    PASSWORD_MISMATCH,
    normalize_person_name,
    normalize_phone_number,
    validate_email_domain_ascii,
    validate_email_length,
    validate_person_name,
    validate_phone_number,
)


class PersonNameField(serializers.CharField):
    """
    Имя/фамилия: значение нормализуется до запуска валидаторов, поэтому
    краевые дефисы и лишние пробелы отсекаются, а не приводят к ошибке.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('validators', [validate_person_name])
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        normalized = normalize_person_name(value)

        if value and not normalized:
            raise serializers.ValidationError(NAME_INVALID_CHARACTERS)

        return normalized


def normalize_user_input(data):
    """Приводит email и номер телефона во входных данных к единому виду."""
    if not isinstance(data, dict):
        return data

    data = data.copy()

    if data.get('email'):
        data['email'] = data['email'].lower()
        data['username'] = data['email']

    if data.get('phone_number'):
        try:
            data['phone_number'] = normalize_phone_number(data['phone_number'])
        except ValidationError as error:
            raise serializers.ValidationError(
                {'phone_number': error.messages}
            ) from error

    return data


class UserBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для профиля (retrieve, put, patch)."""

    avatar = serializers.ImageField(
        required=False,
        # если нужно иметь возможность удалить аватар, добавить allow_null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size,
            validate_avatar_min_resolution,
        ],
    )

    def to_internal_value(self, data):
        return super().to_internal_value(normalize_user_input(data))

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

    first_name = PersonNameField(required=False, allow_blank=True)
    last_name = PersonNameField(required=False, allow_blank=True)
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size,
            validate_avatar_min_resolution,
        ],
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']


class CurrentUserSerializer(UserBaseSerializer):
    """Профиль текущего пользователя для /api/auth/users/me/."""

    class Meta(UserBaseSerializer.Meta):
        extra_kwargs = {
            **UserBaseSerializer.Meta.extra_kwargs,
            'email': {'read_only': True},
            'phone_number': {'read_only': True},
        }


class UserAvatarSerializer(serializers.ModelSerializer):
    """Загрузка аватарки через отдельный эндпоинт /users/me/avatar/."""

    avatar = serializers.ImageField(
        required=True,
        allow_null=False,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_avatar_size,
            validate_avatar_min_resolution,
        ],
    )

    class Meta:
        model = User
        fields = ['avatar']


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

    def validate_password(self, value):
        """Прогоняем пароль через AUTH_PASSWORD_VALIDATORS из настроек.
        DRF сам их не вызывает, поэтому делаем это явно."""
        user = self.instance or User(
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', ''),
        )
        try:
            password_validation.validate_password(value, user)
        except ValidationError as error:
            raise serializers.ValidationError(list(error.messages)) from error
        return value

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + [
            'password',
        ]
        extra_kwargs_add = {
            'password': {'write_only': True, 'trim_whitespace': False},
        }
        extra_kwargs = {**UserBaseSerializer.Meta.extra_kwargs, **extra_kwargs_add}


class UserFullSerializer(UserSelfProfileSerializer):
    """Сериализатор для list, create, delete.
    Полные данные по пользователю."""

    first_name = PersonNameField(required=True, allow_blank=False)
    last_name = PersonNameField(required=True, allow_blank=False)
    email = serializers.EmailField(
        required=True,
        validators=[
            validate_email_length,
            validate_email_domain_ascii,
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует.',
            ),
        ],
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
        return instance.messages_received.filter(
            is_new=True, is_deleted_to=False
        ).count()

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
            instance.messages_received.filter(is_new=True, is_deleted_to=False).count()
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
        max_length=32, validators=[validate_phone_number]
    )

    def to_internal_value(self, data):
        if isinstance(data, dict) and data.get('new_phone_number'):
            data = data.copy()
            try:
                data['new_phone_number'] = normalize_phone_number(
                    data['new_phone_number']
                )
            except ValidationError as error:
                raise serializers.ValidationError(
                    {'new_phone_number': error.messages}
                ) from error
        return super().to_internal_value(data)

    def validate_new_phone_number(self, value):
        user = self.context['request'].user
        if User.objects.filter(phone_number=value).exclude(pk=user.pk).exists():
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

    # Поля объявлены явно, поэтому DRF не добавляет к ним проверку
    # уникальности из модели сам — без нее занятый email или телефон
    # доходит до базы, и djoser подменяет ошибку на общую заглушку.
    phone_number = serializers.CharField(
        required=True,
        validators=[
            validate_phone_number,
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким номером телефона уже существует.',
            ),
        ],
    )
    first_name = PersonNameField(required=True, allow_blank=False)
    last_name = PersonNameField(required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={'input_type': 'password'},
    )
    re_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={'input_type': 'password'},
        error_messages={
            'required': PASSWORD_CONFIRMATION_REQUIRED,
            'blank': PASSWORD_CONFIRMATION_REQUIRED,
            'null': PASSWORD_CONFIRMATION_REQUIRED,
        },
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            validate_email_length,
            validate_email_domain_ascii,
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует.',
            ),
        ],
    )

    def to_internal_value(self, data):
        return super().to_internal_value(normalize_user_input(data))

    def validate_password(self, value):
        """Проверка пароля на уровне поля."""
        user = User(
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', ''),
        )
        try:
            password_validation.validate_password(value, user)
        except ValidationError as error:
            raise serializers.ValidationError(list(error.messages)) from error
        return value

    def validate(self, attrs):
        re_password = attrs.pop('re_password', None)

        if attrs.get('password') != re_password:
            raise serializers.ValidationError({'re_password': PASSWORD_MISMATCH})

        return attrs

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'password',
            're_password',
            'email',
            'phone_number',
            'first_name',
            'last_name',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'trim_whitespace': False},
            'email': {'required': True},
            'phone_number': {'required': True},
            'username': {'required': False},
        }


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False)
    re_new_password = serializers.CharField(trim_whitespace=False)

    def validate(self, data):
        # Проверяем, что пароли совпадают
        if data['new_password'] != data['re_new_password']:
            raise serializers.ValidationError({'re_new_password': PASSWORD_MISMATCH})

        request = self.context.get('request')
        try:
            password_validation.validate_password(
                data['new_password'], getattr(request, 'user', None)
            )
        except ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': error.messages}
            ) from error

        return data
