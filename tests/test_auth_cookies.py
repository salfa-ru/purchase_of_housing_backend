"""Требования к refresh-кукам: HttpOnly, переживает кросс-доменный запрос
и исчезает при выходе. Проверяется на DEBUG=False, то есть в боевом режиме."""

from django.http import HttpResponse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import create_user

LOGIN_URL = '/api/auth/token-auth/'
REFRESH_URL = '/api/auth/token-refresh/'
LOGOUT_URL = '/api/auth/logout/'


class RefreshCookieTest(TestCase):
    """Хранение refresh-токена в HttpOnly cookie."""

    def setUp(self):
        self.client = APIClient()
        self.password = 'Testpass123'
        self.user = create_user('cookieowner', password=self.password)
        self.credentials = {
            'username': self.user.username,
            'password': self.password,
        }

    def login(self):
        return self.client.post(LOGIN_URL, self.credentials, format='json')

    def test_refresh_is_not_returned_in_body(self):
        """Тест: в теле ответа на вход есть access и нет refresh"""
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_cookie_flags(self):
        """Тест: куки HttpOnly, Secure, SameSite=None и на всех путях"""
        cookie = self.login().cookies['refresh_token']

        self.assertTrue(cookie['httponly'])
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'None')
        self.assertEqual(cookie['path'], '/')

    def test_refresh_works_from_cookie_alone(self):
        """Тест: обновление access идет по кукам, без тела запроса"""
        self.login()

        response = self.client.post(REFRESH_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout_clears_cookie_with_same_flags(self):
        """Тест: выход гасит куки теми же атрибутами, что и установка"""
        access = self.login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        response = self.client.post(LOGOUT_URL)
        cookie = response.cookies['refresh_token']

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(cookie.value, '')
        self.assertEqual(cookie['max-age'], 0)
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'None')
        self.assertEqual(cookie['path'], '/')

    def test_refresh_is_rejected_after_logout(self):
        """Тест: отозванный refresh больше не выдает access"""
        access = self.login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.client.post(LOGOUT_URL)
        self.client.credentials()

        response = self.client.post(REFRESH_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(DEBUG=True)
class LocalDevelopmentCookieTest(TestCase):
    """Локально куки нельзя помечать Secure: разработка идет по http."""

    def test_flags_follow_settings(self):
        """Тест: флаги куки берутся из настроек, а не зашиты в коде"""
        from django.conf import settings

        from users.utils import clear_jwt_cookies

        response = HttpResponse()
        clear_jwt_cookies(response)
        cookie = response.cookies['refresh_token']

        self.assertEqual(
            bool(cookie['secure']), settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']
        )
        self.assertEqual(
            cookie['samesite'], settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        )
