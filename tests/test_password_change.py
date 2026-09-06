"""Смена пароля и номера телефона авторизованным пользователем."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_user

SET_PASSWORD_URL = '/api/users/me/set-password/'
CHANGE_PHONE_URL = '/api/users/change-phone/'
LOGIN_URL = '/api/auth/token-auth/'


class SetPasswordTest(TestCase):
    """POST /api/users/me/set-password/"""

    def setUp(self):
        self.client = APIClient()
        self.password = 'Testpass123'
        self.new_password = 'Newpass456'
        self.user = create_user('passwordowner', password=self.password)
        self.client.force_authenticate(self.user)

    def payload(self, **overrides):
        data = {
            'current_password': self.password,
            'new_password': self.new_password,
            're_new_password': self.new_password,
        }
        data.update(overrides)
        return data

    def test_password_is_changed(self):
        """Тест: корректный запрос меняет пароль"""
        response = self.client.post(SET_PASSWORD_URL, self.payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_old_password_stops_working(self):
        """Тест: после смены старый пароль не подходит"""
        self.client.post(SET_PASSWORD_URL, self.payload(), format='json')
        self.user.refresh_from_db()

        self.assertFalse(self.user.check_password(self.password))

    def test_new_password_works_for_login(self):
        """Тест: с новым паролем можно войти"""
        self.client.post(SET_PASSWORD_URL, self.payload(), format='json')

        anonymous = APIClient()
        response = anonymous.post(
            LOGIN_URL,
            {'username': self.user.username, 'password': self.new_password},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mismatched_confirmation_is_rejected(self):
        """Тест: подтверждение не совпадает → 400"""
        response = self.client.post(
            SET_PASSWORD_URL, self.payload(re_new_password='Other123'), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('re_new_password', response.data)

    def test_wrong_current_password_is_rejected(self):
        """Тест: неверный текущий пароль → 400"""
        response = self.client.post(
            SET_PASSWORD_URL, self.payload(current_password='Wrong123'), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)

    def test_same_password_is_rejected(self):
        """Тест: новый пароль совпадает с текущим → 400"""
        response = self.client.post(
            SET_PASSWORD_URL,
            self.payload(new_password=self.password, re_new_password=self.password),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_weak_password_is_rejected(self):
        """Тест: новый пароль без строчных букв → 400"""
        response = self.client.post(
            SET_PASSWORD_URL,
            self.payload(
                new_password='ONLYUPPERCASE123', re_new_password='ONLYUPPERCASE123'
            ),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_anonymous_is_rejected(self):
        """Тест: без авторизации → 401"""
        anonymous = APIClient()

        response = anonymous.post(SET_PASSWORD_URL, self.payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePhoneTest(TestCase):
    """POST /api/users/change-phone/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('phoneowner')
        self.client.force_authenticate(self.user)

    def test_phone_is_changed(self):
        """Тест: номер меняется"""
        response = self.client.post(
            CHANGE_PHONE_URL, {'new_phone_number': '+79991234567'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+79991234567')

    def test_busy_phone_is_rejected(self):
        """Тест: номер занят другим пользователем → 400"""
        other = create_user('otherowner')

        response = self.client.post(
            CHANGE_PHONE_URL, {'new_phone_number': other.phone_number}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_phone_number', response.data)

    def test_anonymous_is_rejected(self):
        """Тест: без авторизации → 401"""
        anonymous = APIClient()

        response = anonymous.post(
            CHANGE_PHONE_URL, {'new_phone_number': '+79991234567'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
