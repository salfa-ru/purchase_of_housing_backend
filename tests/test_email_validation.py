"""Формат адреса электронной почты и связь username с email.

Регрессия на баг «Валидация email»: кириллические и иероглифические домены
принимались, username не был связан с email.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.validators import EMAIL_INVALID

REGISTER_URL = '/api/auth/users/'
User = get_user_model()


class EmailFormatTest(TestCase):
    """Адрес принимается только латиницей."""

    def setUp(self):
        self.client = APIClient()

    def register(self, email, **overrides):
        payload = {
            'email': email,
            'password': 'Qw7zLp4xVn2',
            're_password': 'Qw7zLp4xVn2',
            'first_name': 'Иван',
            'last_name': 'Тестов',
            'phone_number': '+79000000091',
        }
        payload.update(overrides)
        return self.client.post(REGISTER_URL, payload, format='json')

    def assertEmailRejected(self, email):
        response = self.register(email)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )
        self.assertIn('email', response.data)
        self.assertIn(EMAIL_INVALID, response.data['email'])

    def test_cyrillic_domain_is_rejected(self):
        """Кириллический домен не проходит регистрацию"""
        self.assertEmailRejected('user@почта.рф')

    def test_hieroglyphic_domain_is_rejected(self):
        """Иероглифический домен не проходит регистрацию"""
        self.assertEmailRejected('user@邮件.ru')

    def test_punycode_domain_is_rejected(self):
        """Тот же домен в punycode тоже не проходит"""
        self.assertEmailRejected('user@xn--80a1acny.xn--p1ai')

    def test_cyrillic_local_part_is_rejected(self):
        """Кириллица до собачки не проходит (ловит штатный валидатор)"""
        self.assertEmailRejected('пользователь@mail.ru')

    def test_single_error_message_is_returned(self):
        """На кириллический домен приходит ровно одно сообщение"""
        response = self.register('user@почта.рф')

        self.assertEqual(response.data['email'], [EMAIL_INVALID])

    def test_ordinary_email_is_accepted(self):
        """Обычный адрес по-прежнему принимается"""
        response = self.register('user@mail.ru')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_domain_with_xn_inside_label_is_accepted(self):
        """Xn-- режется только в начале метки домена"""
        response = self.register('user@my-xn--domain.ru')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)


class UsernameFromEmailTest(TestCase):
    """username скрыт от пользователя и всегда равен email."""

    def setUp(self):
        self.client = APIClient()

    def register(self, email, **overrides):
        payload = {
            'email': email,
            'password': 'Qw7zLp4xVn2',
            're_password': 'Qw7zLp4xVn2',
            'first_name': 'Иван',
            'last_name': 'Тестов',
            'phone_number': '+79000000092',
        }
        payload.update(overrides)
        return self.client.post(REGISTER_URL, payload, format='json')

    def test_custom_username_is_replaced_by_email(self):
        """Присланный username подменяется адресом почты"""
        email = 'user_mismatch@mail.ru'

        response = self.register(email, username='custom_username')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], email)
        self.assertEqual(User.objects.get(email=email).username, email)
        self.assertFalse(User.objects.filter(username='custom_username').exists())

    def test_registration_without_username_works(self):
        """Username можно не присылать вовсе"""
        email = 'nousername@mail.ru'

        response = self.register(email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], email)

    def test_username_of_another_user_does_not_block_registration(self):
        """Чужой username в запросе не мешает — он все равно не сохранится"""
        self.register('first@mail.ru')

        response = self.register(
            'second@mail.ru', username='first@mail.ru', phone_number='+79000000093'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], 'second@mail.ru')

    def test_email_and_username_are_lowercased(self):
        """Адрес в верхнем регистре приводится к нижнему вместе с username"""
        response = self.register('Ivan@Ya.RU')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['email'], 'ivan@ya.ru')
        self.assertEqual(response.data['username'], 'ivan@ya.ru')
