import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# ========== ВАЛИДАТОР ИМЕНИ ==========


def validate_person_name(value):
    """
    Проверяет, что имя/фамилия содержит только кириллицу, пробел, тире, дефис (2-40 символов).
    """
    if not value:
        raise ValidationError(
            'Поле не может быть пустым.',
            code='required',
        )

    # Удаляем лишние пробелы
    value = value.strip()

    # Проверяем длину
    if len(value) < 2 or len(value) > 40:
        raise ValidationError(
            'Длина должна быть от 2 до 40 символов.',
            code='invalid_length',
        )

    # Проверяем допустимые символы
    # Кириллица: \u0400-\u04FF (А-Яа-я), \u0500-\u052F (Ёё и др.)
    pattern = r'^[\u0400-\u04FF\u0500-\u052F \-—]{2,40}$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Введены недопустимые символы. Только кириллица, пробел, тире, дефис, от 2 до 40 символов.',
            code='invalid_characters',
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


class LetterAndDigitPasswordValidator:
    """Пароль должен содержать минимум одну латинскую букву и одну цифру."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну латинскую букву.',
                code='password_no_letter',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну цифру.',
                code='password_no_digit',
            )

    def get_help_text(self):
        return 'Пароль должен содержать минимум одну латинскую букву и одну цифру.'


# ========== ВАЛИДАТОР ЗАГЛАВНЫХ БУКВ (ДЛЯ #28348) ==========


class ContainsUppercaseValidator:
    """Проверяет, что пароль содержит хотя бы одну заглавную букву."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну заглавную букву.',
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return 'Пароль должен содержать хотя бы одну заглавную букву.'


class MaximumLengthPasswordValidator:
    """Проверяет, что пароль не длиннее заданного предела."""

    def __init__(self, max_length=60):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                f'Пароль не должен превышать {self.max_length} символов.',
                code='password_too_long',
            )

    def get_help_text(self):
        return f'Пароль не должен превышать {self.max_length} символов.'
