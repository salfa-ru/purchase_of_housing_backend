import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# ========== ВАЛИДАТОР ИМЕНИ ==========

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 50

# Кириллица: \u0400-\u04FF (А-Яа-я), \u0500-\u052F (Ёё и др.)
NAME_PATTERN = r'^[A-Za-z\u0400-\u04FF\u0500-\u052F \-—]+$'
NAME_LETTER_PATTERN = r'[A-Za-z\u0400-\u04FF\u0500-\u052F]'


def validate_person_name(value):
    """
    Проверяет имя/фамилию: буквы кириллицы и латиницы, пробел, тире, дефис,
    от 2 до 50 символов.
    """
    if not value:
        raise ValidationError(
            'Поле не может быть пустым.',
            code='required',
        )

    # Удаляем лишние пробелы
    value = value.strip()

    # Проверяем длину
    if len(value) < NAME_MIN_LENGTH or len(value) > NAME_MAX_LENGTH:
        raise ValidationError(
            f'Длина должна быть от {NAME_MIN_LENGTH} до {NAME_MAX_LENGTH} символов.',
            code='invalid_length',
        )

    # Проверяем допустимые символы
    if not re.match(NAME_PATTERN, value):
        raise ValidationError(
            'Введены недопустимые символы. Только буквы, пробел, тире, дефис, '
            f'от {NAME_MIN_LENGTH} до {NAME_MAX_LENGTH} символов.',
            code='invalid_characters',
        )

    if not re.search(NAME_LETTER_PATTERN, value):
        raise ValidationError(
            'Имя должно содержать хотя бы одну букву.',
            code='no_letters',
        )

    return value


# ========== ВАЛИДАТОР ТЕЛЕФОНА ==========

validate_phone_number = RegexValidator(
    regex=r'^(\+7|8)\d{10}$',
    message='Введите номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX.',
)

PHONE_NUMBER_ERROR = (
    'Введите номер телефона в формате +7XXXXXXXXXX, 8XXXXXXXXXX '
    'или 10 цифр без кода страны.'
)


def normalize_phone_number(value):
    """
    Приводит номер к виду +7XXXXXXXXXX.
    Принимает 10 цифр, 8..., 7..., +7... — с пробелами, скобками и дефисами.
    """
    if not value:
        return value

    value = str(value).strip()
    digits = re.sub(r'\D', '', value)

    if len(digits) == 11 and digits[0] in ('7', '8'):
        digits = f'7{digits[1:]}'
    elif len(digits) == 10 and not value.startswith('+'):
        digits = f'7{digits}'
    else:
        raise ValidationError(PHONE_NUMBER_ERROR, code='invalid_phone_number')

    return f'+{digits}'


# ========== ВАЛИДАТОР EMAIL ==========

EMAIL_MAX_LENGTH = 254  # RFC 5321: вся строка адреса
EMAIL_LOCAL_MAX_LENGTH = 64  # RFC 5321: часть до @
EMAIL_DOMAIN_MAX_LENGTH = 255  # RFC 5321: часть после @


def validate_email_length(value):
    """
    Проверяет длину частей адреса электронной почты по RFC 5321/5322.
    """
    if not value:
        return value

    if len(value) > EMAIL_MAX_LENGTH:
        raise ValidationError(
            f'Адрес электронной почты не должен превышать {EMAIL_MAX_LENGTH} символов.',
            code='email_too_long',
        )

    local_part, _, domain_part = value.rpartition('@')

    if len(local_part) > EMAIL_LOCAL_MAX_LENGTH:
        raise ValidationError(
            f'Часть адреса до символа @ не должна превышать {EMAIL_LOCAL_MAX_LENGTH} символов.',
            code='email_local_too_long',
        )

    if len(domain_part) > EMAIL_DOMAIN_MAX_LENGTH:
        raise ValidationError(
            f'Доменная часть адреса не должна превышать {EMAIL_DOMAIN_MAX_LENGTH} символов.',
            code='email_domain_too_long',
        )

    return value


# ========== ВАЛИДАТОР ПАРОЛЯ ==========

PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 60

PASSWORD_REQUIREMENTS = (
    f'Пароль должен содержать не менее {PASSWORD_MIN_LENGTH} и не более '
    f'{PASSWORD_MAX_LENGTH} символов, заглавные и строчные латинские буквы, цифры.'
)


class PasswordComplexityValidator:
    """Все требования к паролю разом: длина, заглавные и строчные латинские
    буквы, цифры. Спецсимволы допустимы."""

    def __init__(self, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        if (
            not self.min_length <= len(password) <= self.max_length
            or not re.search(r'[A-Z]', password)
            or not re.search(r'[a-z]', password)
            or not re.search(r'[0-9]', password)
        ):
            raise ValidationError(
                PASSWORD_REQUIREMENTS,
                code='password_requirements',
            )

    def get_help_text(self):
        return PASSWORD_REQUIREMENTS
