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
