"""Требования к паролю: 6-60 символов, обязательны заглавные и
строчные латинские буквы и цифры. Спецсимволы допустимы, пробелы и любые
символы вне латиницы — нет. Каждое нарушение описывается своим сообщением,
все найденные приходят списком."""

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.serializers import UserFullSerializer
from users.validators import (
    PASSWORD_CONFIRMATION_REQUIRED,
    PASSWORD_INVALID_CHARACTERS,
    PASSWORD_MISMATCH,
    PASSWORD_NO_DIGIT,
    PASSWORD_NO_LOWERCASE,
    PASSWORD_NO_UPPERCASE,
    PASSWORD_REQUIREMENTS,
    password_too_long,
    password_too_short,
)

REGISTER_URL = '/api/auth/users/'
User = get_user_model()


class PasswordRulesTest(TestCase):
    """Набор AUTH_PASSWORD_VALIDATORS целиком."""

    def assertRejected(self, password, *expected_messages):
        try:
            password_validation.validate_password(password)
        except ValidationError as error:
            for message in expected_messages:
                self.assertIn(
                    message,
                    error.messages,
                    f'пароль {password!r} отклонен, но без сообщения {message!r}',
                )
        else:
            self.fail(f'пароль {password!r} принят, хотя должен быть отклонен')

    def test_uppercase_only_is_rejected(self):
        """Тест: пароль из одних заглавных → нужна строчная буква"""
        self.assertRejected('ONLYUPPERCASE123', PASSWORD_NO_LOWERCASE)

    def test_lowercase_only_is_rejected(self):
        """Тест: пароль из одних строчных → нужна заглавная буква"""
        self.assertRejected('onlylowercase123', PASSWORD_NO_UPPERCASE)

    def test_letters_without_digits_are_rejected(self):
        """Тест: пароль без цифр → нужна цифра"""
        self.assertRejected('OnlyLetters', PASSWORD_NO_DIGIT)

    def test_cyrillic_does_not_count_as_letters(self):
        """Тест: кириллица не заменяет латинские буквы"""
        self.assertRejected(
            'Пароль123',
            PASSWORD_NO_UPPERCASE,
            PASSWORD_NO_LOWERCASE,
            PASSWORD_INVALID_CHARACTERS,
        )

    def test_digits_only_is_rejected(self):
        """Тест: пароль из одних цифр → нужны буквы обоих регистров"""
        self.assertRejected('1234567', PASSWORD_NO_UPPERCASE, PASSWORD_NO_LOWERCASE)

    def test_too_short_is_rejected(self):
        """Тест: пароль короче 6 символов → сообщение про длину"""
        self.assertRejected('Ab1cd', password_too_short())

    def test_too_long_is_rejected(self):
        """Тест: пароль длиннее 60 символов → сообщение про длину"""
        self.assertRejected('Ab1' + 'c' * 58, password_too_long())

    def test_short_password_does_not_complain_about_characters(self):
        """Тест: у короткого, но полного по составу пароля одна претензия"""
        with self.assertRaises(ValidationError) as context:
            password_validation.validate_password('Ab1cd')

        self.assertEqual(context.exception.messages, [password_too_short()])

    def test_six_characters_is_enough(self):
        """Тест: шести символов достаточно"""
        password_validation.validate_password('Ab1cd2')

    def test_sixty_characters_are_allowed(self):
        """Тест: шестьдесят символов еще допустимы"""
        password_validation.validate_password('Ab1' + 'c' * 57)

    def test_special_characters_are_allowed(self):
        """Тест: спецсимволы не мешают"""
        password_validation.validate_password('Passw0rd!')

    def test_example_from_specification_is_accepted(self):
        """Тест: пример корректного пароля из ТЗ принимается"""
        password_validation.validate_password('123456789qQ')

    def test_help_text_lists_all_requirements(self):
        """Тест: подсказка в документации перечисляет требования целиком"""
        self.assertIn(
            PASSWORD_REQUIREMENTS, password_validation.password_validators_help_texts()
        )


class PasswordRulesApiTest(TestCase):
    """Правила применяются на обеих точках создания пользователя."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'err7@mail.ru',
            'username': 'err7@mail.ru',
            'first_name': 'Игорь',
            'last_name': 'Тест',
            'phone_number': '+79000000012',
            'password': 'onlylowercase123',
            're_password': 'onlylowercase123',
        }

    def test_registration_rejects_password_without_uppercase(self):
        """Тест: POST /api/auth/users/ → 400 с указанием, чего не хватает"""
        response = self.client.post(REGISTER_URL, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_NO_UPPERCASE, response.data['password'])

    def test_dev_serializer_rejects_password_without_uppercase(self):
        """Тест: сериализатор dev-эндпоинта не пропускает такой пароль"""
        serializer = UserFullSerializer(data=self.payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_valid_password_is_accepted(self):
        """Тест: пароль по правилам → пользователь создается"""
        self.payload['password'] = '123456789qQ'
        self.payload['re_password'] = '123456789qQ'

        response = self.client.post(REGISTER_URL, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PasswordCharactersTest(TestCase):
    """Состав символов: только латиница, цифры и спецсимволы."""

    def assertRejected(self, password):
        with self.assertRaises(ValidationError) as context:
            password_validation.validate_password(password)

        self.assertIn(
            PASSWORD_INVALID_CHARACTERS,
            context.exception.messages,
            f'пароль {password!r} отклонен, но без претензии к символам',
        )

    def test_leading_space_is_rejected(self):
        """Пробел в начале пароля недопустим"""
        self.assertRejected(' Ab1cd2')

    def test_trailing_space_is_rejected(self):
        """Пробел в конце пароля недопустим"""
        self.assertRejected('Ab1cd2 ')

    def test_inner_space_is_rejected(self):
        """Пробел внутри пароля недопустим"""
        self.assertRejected('Ab1 cd2')

    def test_tab_is_rejected(self):
        """Табуляция недопустима"""
        self.assertRejected('Ab1\tcd2')

    def test_emoji_is_rejected(self):
        """Эмодзи недопустимы"""
        self.assertRejected('Ab1cd2😀')

    def test_hieroglyph_is_rejected(self):
        """Иероглифы недопустимы"""
        self.assertRejected('Ab1cd2漢字')

    def test_cyrillic_letter_is_rejected(self):
        """Кириллическая буква среди латинских недопустима"""
        self.assertRejected('AbВ1cd2')

    def test_all_special_characters_are_allowed(self):
        """Спецсимволы латинской раскладки разрешены"""
        password_validation.validate_password('Ab1!"#$%&\'()*+,-./:;<=>?@[]^_`{|}~')

    def test_ordinary_password_is_not_affected(self):
        """Обычный пароль правилами не задет"""
        password_validation.validate_password('Passw0rd!')


class PasswordCharactersApiTest(TestCase):
    """Проверка состава символов работает на регистрации."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'err8@mail.ru',
            'first_name': 'Игорь',
            'last_name': 'Тест',
            'phone_number': '+79000000015',
            'password': '123456789qQ',
            're_password': '123456789qQ',
        }

    def register(self, password):
        self.payload['password'] = password
        self.payload['re_password'] = password
        return self.client.post(REGISTER_URL, self.payload, format='json')

    def test_password_with_space_is_rejected(self):
        """Тест: POST /api/auth/users/ с пробелом в пароле → 400"""
        response = self.register('12345 6789qQ')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_INVALID_CHARACTERS, response.data['password'])

    def test_password_with_leading_space_is_rejected(self):
        """Пробел в начале не срезается, а дает 400"""
        response = self.register(' 123456789qQ')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_INVALID_CHARACTERS, response.data['password'])

    def test_password_with_trailing_space_is_rejected(self):
        """Пробел в конце не срезается, а дает 400"""
        response = self.register('123456789qQ ')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_INVALID_CHARACTERS, response.data['password'])

    def test_password_with_emoji_is_rejected(self):
        """Тест: POST /api/auth/users/ с эмодзи в пароле → 400"""
        response = self.register('123456789qQ😀')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_INVALID_CHARACTERS, response.data['password'])

    def test_password_with_hieroglyph_is_rejected(self):
        """Тест: POST /api/auth/users/ с иероглифом в пароле → 400"""
        response = self.register('123456789qQ漢')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_INVALID_CHARACTERS, response.data['password'])

    def test_valid_password_still_works(self):
        """Тест: корректный пароль по-прежнему проходит"""
        response = self.register('123456789qQ')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)


class PasswordConfirmationTest(TestCase):
    """re_password обязателен и должен совпадать с password."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            'email': 'err9@mail.ru',
            'first_name': 'Игорь',
            'last_name': 'Тест',
            'phone_number': '+79000000016',
            'password': '123456789qQ',
            're_password': '123456789qQ',
        }

    def register(self, **overrides):
        payload = dict(self.payload)
        for field, value in overrides.items():
            if value is None:
                payload.pop(field, None)
            else:
                payload[field] = value
        return self.client.post(REGISTER_URL, payload, format='json')

    def test_matching_confirmation_is_accepted(self):
        """Тест: совпадающее подтверждение → пользователь создается"""
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_mismatching_confirmation_is_rejected(self):
        """Тест: пароли не совпадают → 400 с понятным текстом"""
        response = self.register(re_password='123456789qW')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_MISMATCH, response.data['re_password'])

    def test_missing_confirmation_is_rejected(self):
        """Тест: без подтверждения регистрация не проходит"""
        response = self.register(re_password=None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_CONFIRMATION_REQUIRED, response.data['re_password'])

    def test_blank_confirmation_is_rejected(self):
        """Тест: пустое подтверждение не проходит"""
        response = self.register(re_password='')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(PASSWORD_CONFIRMATION_REQUIRED, response.data['re_password'])

    def test_confirmation_is_not_stored(self):
        """Тест: re_password не попадает ни в ответ, ни в базу"""
        response = self.register()

        self.assertNotIn('re_password', response.data)
        user = User.objects.get(email=self.payload['email'])
        self.assertTrue(user.check_password(self.payload['password']))
