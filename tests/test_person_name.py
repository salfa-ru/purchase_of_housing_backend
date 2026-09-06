"""Валидация имени и фамилии: буквы кириллицы и латиницы, пробелы
и дефисы, 2-50 символов, автоматическая капитализация."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_user
from users.serializers import capitalize_name
from users.validators import validate_person_name

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
        """Тест: кириллица принимается"""
        self.assertAccepted('Игорь')

    def test_latin_is_accepted(self):
        """Тест: латиница принимается"""
        self.assertAccepted('John')

    def test_hyphenated_name_is_accepted(self):
        """Тест: двойное имя через дефис принимается"""
        self.assertAccepted('Анна-Мария')

    def test_name_with_space_is_accepted(self):
        """Тест: составное имя с пробелами принимается"""
        self.assertAccepted('Ван Дер Берг')

    def test_fifty_characters_are_allowed(self):
        """Тест: пятьдесят символов еще допустимы"""
        self.assertAccepted('и' * 50)

    def test_longer_than_fifty_is_rejected(self):
        """Тест: пятьдесят один символ отклоняется"""
        self.assertRejected('и' * 51)

    def test_single_character_is_rejected(self):
        """Тест: один символ отклоняется"""
        self.assertRejected('И')

    def test_digits_are_rejected(self):
        """Тест: цифры в имени отклоняются"""
        self.assertRejected('Иван1')

    def test_special_characters_are_rejected(self):
        """Тест: спецсимволы отклоняются"""
        self.assertRejected('Иван@')

    def test_separators_only_are_rejected(self):
        """Тест: имя из одних разделителей отклоняется"""
        self.assertRejected('--')


class NameCapitalizationTest(TestCase):
    """Автоматическая капитализация."""

    def test_lowercase_is_capitalized(self):
        """Тест: первая буква поднимается до заглавной"""
        self.assertEqual(capitalize_name('игорь'), 'Игорь')

    def test_uppercase_is_normalized(self):
        """Тест: имя капсом приводится к обычному виду"""
        self.assertEqual(capitalize_name('ИГОРЬ'), 'Игорь')

    def test_each_part_of_hyphenated_name(self):
        """Тест: капитализируется каждая часть имени через дефис"""
        self.assertEqual(capitalize_name('анна-мария'), 'Анна-Мария')

    def test_each_word_of_compound_name(self):
        """Тест: капитализируется каждое слово составного имени"""
        self.assertEqual(capitalize_name('ван дер берг'), 'Ван Дер Берг')

    def test_double_hyphen_is_collapsed(self):
        """Тест: двойной дефис схлопывается в один"""
        self.assertEqual(capitalize_name('анна--мария'), 'Анна-Мария')


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
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': '+79000000014',
            },
            format='json',
        )

    def test_name_is_capitalized_on_registration(self):
        """Тест: при регистрации имя и фамилия капитализируются"""
        response = self.register('игорь', 'петров-водкин')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Игорь')
        self.assertEqual(response.data['last_name'], 'Петров-Водкин')

    def test_latin_name_is_accepted_on_registration(self):
        """Тест: латинское имя проходит регистрацию"""
        response = self.register('john', 'smith')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'John')

    def test_name_with_digits_is_rejected_on_registration(self):
        """Тест: имя с цифрами не проходит регистрацию"""
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
        """Тест: при обновлении профиля имя и фамилия капитализируются"""
        response = self.patch_name(first_name='анна--мария', last_name='ван дер берг')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Анна-Мария')
        self.assertEqual(response.data['last_name'], 'Ван Дер Берг')

    def test_name_with_digits_is_rejected_on_update(self):
        """Тест: имя с цифрами не проходит обновление профиля"""
        response = self.patch_name(first_name='Иван1')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_longer_than_fifty_is_rejected_on_update(self):
        """Тест: пятьдесят один символ не проходит обновление профиля"""
        response = self.patch_name(first_name='и' * 51)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_fifty_characters_are_allowed_on_update(self):
        """Тест: пятьдесят символов проходят обновление профиля"""
        response = self.patch_name(first_name='и' * 50)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blank_last_name_is_allowed(self):
        """Тест: фамилию можно очистить"""
        response = self.patch_name(last_name='')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'], '')
