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


# ========== ВАЛИДАТОР ПАРОЛЯ ==========


class PasswordComplexityValidator:
    """Пароль должен содержать строчные и заглавные латинские буквы и цифры."""

    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну строчную латинскую букву.',
                code='password_no_lower',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну заглавную латинскую букву.',
                code='password_no_upper',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                'Пароль должен содержать хотя бы одну цифру.',
                code='password_no_digit',
            )

    def get_help_text(self):
        return 'Пароль должен содержать строчные и заглавные латинские буквы и цифры.'


class MaximumLengthPasswordValidator:
    """Пароль не должен превышать заданную длину."""

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
