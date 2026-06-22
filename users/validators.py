from django.core.validators import RegexValidator

validate_person_name = RegexValidator(
    regex=r'^[А-Яа-яЁё \-—]{2,40}$',
    message=(
        'Введены недопустимые символы. '
        'Только кириллица, пробел, тире, дефис, от 2 до 40 символов.'
    ),
)
