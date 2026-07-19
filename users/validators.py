import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

validate_person_name = RegexValidator(
    regex=r'^[А-Яа-яЁё \-—]{2,40}$',
    message=(
        'Введены недопустимые символы. '
        'Только кириллица, пробел, тире, дефис, от 2 до 40 символов.'
    ),
)

validate_phone_number = RegexValidator(
    regex=r'^(\+7|8)\d{10}$',
    message='Введите номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX.',
)


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
