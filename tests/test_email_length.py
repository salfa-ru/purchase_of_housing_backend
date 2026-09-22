"""Длина адреса электронной почты по ТЗ."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

REGISTER_URL = '/api/auth/users/'
User = get_user_model()


def make_email(total_length):
    """Синтаксически корректный адрес заданной длины."""
    local = 'a' * 64
    remaining = total_length - len(local) - 1
    labels = []
    while remaining > 3:
        size = min(63, remaining - 1) if remaining - 1 > 63 else remaining - 3
        labels.append('b' * size)
        remaining -= size + 1
    return f'{local}@' + '.'.join(labels) + '.ru'


class EmailLengthTest(TestCase):
    """Границы длины адреса на регистрации."""

    def setUp(self):
        self.client = APIClient()

    def register(self, email):
        return self.client.post(
            REGISTER_URL,
            {
                'username': email,
                'email': email,
                'password': 'Ab1cd2',
                're_password': 'Ab1cd2',
                'first_name': 'Тест',
                'last_name': 'Тест',
                'phone_number': '+79000000013',
            },
            format='json',
        )

    def test_email_of_254_characters_is_accepted(self):
        """Тест: адрес ровно в 254 символа принимается"""
        email = make_email(254)
        self.assertEqual(len(email), 254)

        response = self.register(email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_long_email_is_stored_in_username(self):
        """Тест: длинный адрес целиком доезжает до username в базе"""
        email = make_email(254)

        self.register(email)
        user = User.objects.get(email=email)

        self.assertEqual(user.username, email)

    def test_email_longer_than_254_is_rejected(self):
        """Тест: адрес длиннее 254 символов отклоняется"""
        response = self.register(make_email(255))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_long_local_part_is_accepted(self):
        """Тест: длинная часть до @ не мешает регистрации (кейс из баги)"""
        email = 'a123456789' * 24 + '435daad@ya.ru'
        self.assertEqual(len(email), 253)

        response = self.register(email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_email_shorter_than_6_is_rejected(self):
        """Тест: адрес короче 6 символов отклоняется"""
        email = 'a@b.c'
        self.assertEqual(len(email), 5)

        response = self.register(email)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_ordinary_email_still_works(self):
        """Тест: обычный короткий адрес не задет правками"""
        response = self.register('v@ya.ru')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
