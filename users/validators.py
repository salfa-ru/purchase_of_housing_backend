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
