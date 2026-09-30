"""Валидация имени и фамилии: только кириллица, пробелы и дефисы,
2-40 символов, автоматическая нормализация."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_user
from users.serializers import UserFullSerializer
from users.validators import (
    NAME_INVALID_CHARACTERS,
    normalize_person_name,
    validate_person_name,
)

REGISTER_URL = '/api/auth/users/'
PROFILE_URL = '/api/users/profile/'


class PersonNameValidationTest(TestCase):
    """Допустимые символы и длина."""

    def assertAccepted(self, value):
        validate_person_name(value)

    def assertRejected(self, value):
        with self.assertRaises(ValidationError, msg=f'{value!r} должно отклоняться'):
            validate_person_name(value)

    def test_cyrillic_is_accepted(self):
        """Кириллица принимается"""
        self.assertAccepted('Игорь')

    def test_latin_is_rejected(self):
        """Латиница не принимается"""
        self.assertRejected('John')

    def test_mixed_alphabets_are_rejected(self):
        """Смесь кириллицы и латиницы не принимается"""
        self.assertRejected('Иванoff')

    def test_tab_is_rejected(self):
        """Табуляция не принимается"""
        self.assertRejected(normalize_person_name('Иван\tИван'))

    def test_line_break_is_rejected(self):
        """Перенос строки не принимается"""
        self.assertRejected(normalize_person_name('Иван\nИван'))

    def test_hyphenated_name_is_accepted(self):
        """Двойное имя через дефис принимается"""
        self.assertAccepted('Анна-Мария')

    def test_name_with_space_is_accepted(self):
        """Составное имя с пробелами принимается"""
        self.assertAccepted('Ван Дер Берг')

    def test_forty_characters_are_allowed(self):
        """Сорок символов еще допустимы"""
        self.assertAccepted('и' * 40)

    def test_longer_than_forty_is_rejected(self):
        """Сорок один символ отклоняется"""
        self.assertRejected('и' * 41)

    def test_single_character_is_rejected(self):
        """Один символ отклоняется"""
        self.assertRejected('И')

    def test_digits_are_rejected(self):
        """Цифры в имени отклоняются"""
        self.assertRejected('Иван1')

    def test_special_characters_are_rejected(self):
        """Спецсимволы отклоняются"""
        self.assertRejected('Иван@')

    def test_separators_only_are_rejected(self):
        """Имя из одних разделителей отклоняется"""
        self.assertRejected('--')

    def test_normalized_separators_only_are_rejected(self):
        """Строка из дефисов после нормализации пуста и отклоняется"""
        for value in ('-', '-—-'):
            with self.subTest(value=value):
                self.assertRejected(normalize_person_name(value))


class NameCapitalizationTest(TestCase):
    """Автоматическая капитализация."""

    def test_lowercase_is_capitalized(self):
        """Первая буква поднимается до заглавной"""
        self.assertEqual(normalize_person_name('игорь'), 'Игорь')

    def test_uppercase_is_normalized(self):
        """Имя капсом приводится к обычному виду"""
        self.assertEqual(normalize_person_name('ИГОРЬ'), 'Игорь')

    def test_each_part_of_hyphenated_name(self):
        """Капитализируется каждая часть имени через дефис"""
        self.assertEqual(normalize_person_name('анна-мария'), 'Анна-Мария')

    def test_each_word_of_compound_name(self):
        """Капитализируется каждое слово составного имени"""
        self.assertEqual(normalize_person_name('ван дер берг'), 'Ван Дер Берг')

    def test_double_hyphen_is_collapsed(self):
        """Двойной дефис схлопывается в один"""
        self.assertEqual(normalize_person_name('анна--мария'), 'Анна-Мария')

    def test_leading_hyphen_is_stripped(self):
        """Дефис в начале имени срезается"""
        self.assertEqual(normalize_person_name('-иван'), 'Иван')

    def test_trailing_hyphen_is_stripped(self):
        """Дефис в конце имени срезается"""
        self.assertEqual(normalize_person_name('иван-'), 'Иван')

    def test_surrounding_dashes_are_stripped(self):
        """Тире по краям имени срезается"""
        self.assertEqual(normalize_person_name('—иван—'), 'Иван')

    def test_surrounding_spaces_are_stripped(self):
        """Пробелы по краям имени срезаются"""
        self.assertEqual(normalize_person_name(' игорь '), 'Игорь')


class NameOnRegistrationTest(TestCase):
    """Имя приходит в базу уже капитализированным."""

    def setUp(self):
        self.client = APIClient()

    def register(self, first_name, last_name):
        return self.client.post(
            REGISTER_URL,
            {
                'username': 'nameowner@test.com',
                'email': 'nameowner@test.com',
                'password': '123456789qQ',
                're_password': '123456789qQ',
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': '+79000000014',
            },
            format='json',
        )

    def test_name_is_capitalized_on_registration(self):
        """При регистрации имя и фамилия капитализируются"""
        response = self.register('игорь', 'петров-водкин')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Игорь')
        self.assertEqual(response.data['last_name'], 'Петров-Водкин')

    def test_latin_name_is_rejected_on_registration(self):
        """Латинское имя не проходит регистрацию"""
        response = self.register('john', 'smith')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(NAME_INVALID_CHARACTERS, response.data['first_name'])

    def test_tab_in_name_is_rejected_on_registration(self):
        """Табуляция в имени не проходит регистрацию"""
        response = self.register('Иван\tИван', 'Тест')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(NAME_INVALID_CHARACTERS, response.data['first_name'])

    def test_line_break_in_name_is_rejected_on_registration(self):
        """Перенос строки в имени не проходит регистрацию"""
        response = self.register('Иван\nИван', 'Тест')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(NAME_INVALID_CHARACTERS, response.data['first_name'])

    def test_edge_hyphens_are_stripped_on_registration(self):
        """Дефисы по краям имени и фамилии срезаются при регистрации"""
        response = self.register('-Иван', 'Тест-')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Иван')
        self.assertEqual(response.data['last_name'], 'Тест')

    def test_name_with_digits_is_rejected_on_registration(self):
        """Имя с цифрами не проходит регистрацию"""
        response = self.register('Иван1', 'Тест')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)


class NameOnProfileUpdateTest(TestCase):
    """PATCH профиля подчиняется тем же правилам, что и регистрация."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=create_user('nameprofile'))

    def patch_name(self, **payload):
        return self.client.patch(PROFILE_URL, payload, format='json')

    def test_name_is_capitalized_on_update(self):
        """При обновлении профиля имя и фамилия капитализируются"""
        response = self.patch_name(first_name='анна--мария', last_name='ван дер берг')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Анна-Мария')
        self.assertEqual(response.data['last_name'], 'Ван Дер Берг')

    def test_name_with_digits_is_rejected_on_update(self):
        """Имя с цифрами не проходит обновление профиля"""
        response = self.patch_name(first_name='Иван1')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_longer_than_forty_is_rejected_on_update(self):
        """Сорок один символ не проходит обновление профиля"""
        response = self.patch_name(first_name='и' * 41)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_forty_characters_are_allowed_on_update(self):
        """Сорок символов проходят обновление профиля"""
        response = self.patch_name(first_name='и' * 40)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blank_last_name_is_allowed(self):
        """Фамилию можно очистить"""
        response = self.patch_name(last_name='')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'], '')


class NameOnDevRegistrationTest(TestCase):
    """Регрессия на баг: /api/users/dev/ принимал имя с дефисом по краям.

    Роут dev подключается только при DEBUG=True (users/urls.py), поэтому
    проверяем сериализатор, на котором он работает.
    """

    def serialize(self, first_name, last_name):
        serializer = UserFullSerializer(
            data={
                'username': 'devnameowner@test.com',
                'email': 'devnameowner@test.com',
                'password': '123456789qQ',
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': '+79000000015',
            }
        )
        return serializer

    def assertNormalized(self, first_name, last_name, expected_first, expected_last):
        serializer = self.serialize(first_name, last_name)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['first_name'], expected_first)
        self.assertEqual(serializer.validated_data['last_name'], expected_last)

    def test_leading_hyphen_is_stripped(self):
        """'-Иван' проходит и сохраняется как 'Иван'"""
        self.assertNormalized('-Иван', 'Тест', 'Иван', 'Тест')

    def test_trailing_hyphen_is_stripped(self):
        """'Иван-' проходит и сохраняется как 'Иван'"""
        self.assertNormalized('Иван-', 'Тест-', 'Иван', 'Тест')

    def test_name_is_capitalized(self):
        """На dev-эндпоинте имя тоже капитализируется"""
        self.assertNormalized(
            'иван--иван', 'петров-водкин', 'Иван-Иван', 'Петров-Водкин'
        )

    def test_hyphen_only_name_is_rejected(self):
        """Имя из одного дефиса отклоняется как недопустимые символы"""
        serializer = self.serialize('-', 'Тест')

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['first_name'], [NAME_INVALID_CHARACTERS])
