"""Требования к refresh-кукам: HttpOnly, переживает кросс-доменный запрос
и исчезает при выходе. Плюс порядок чтения refresh-токена на обновлении:
сначала тело запроса, потом кука. Проверяется на DEBUG=False, то есть
в боевом режиме."""

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
        """В теле ответа на вход есть access и нет refresh"""
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_cookie_flags(self):
        """Куки HttpOnly, Secure, SameSite=None и на всех путях"""
        cookie = self.login().cookies['refresh_token']

        self.assertTrue(cookie['httponly'])
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'None')
        self.assertEqual(cookie['path'], '/')

    def test_refresh_works_from_cookie_alone(self):
        """Обновление access идет по кукам, без тела запроса"""
        self.login()

        response = self.client.post(REFRESH_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout_clears_cookie_with_same_flags(self):
        """Выход гасит куки теми же атрибутами, что и установка"""
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
        """Отозванный refresh больше не выдает access"""
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
        """Флаги куки берутся из настроек, а не зашиты в коде"""
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


class RefreshTokenSourceTest(TestCase):
    """Откуда берется refresh на /api/auth/token-refresh/."""

    def setUp(self):
        self.client = APIClient()
        self.password = 'Testpass123'
        self.user = create_user('refreshsource', password=self.password)
        self.other_user = create_user('refreshother', password=self.password)

    def login(self, user):
        return self.client.post(
            LOGIN_URL,
            {'username': user.username, 'password': self.password},
            format='json',
        )

    def refresh_token_of(self, user):
        """Свежий refresh-токен пользователя, без следов в куках клиента."""
        client = APIClient()
        client.post(
            LOGIN_URL,
            {'username': user.username, 'password': self.password},
            format='json',
        )
        return client.cookies['refresh_token'].value

    def test_body_token_is_accepted_without_cookie(self):
        """Токен из тела работает, когда куки нет"""
        token = self.refresh_token_of(self.user)

        response = self.client.post(REFRESH_URL, {'refresh': token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_body_token_wins_over_cookie(self):
        """Тело запроса важнее куки"""
        self.login(self.user)
        # только ASCII: куки кодируются в latin-1
        self.client.cookies['refresh_token'] = 'broken-token-from-cookie'
        token = self.refresh_token_of(self.other_user)

        response = self.client.post(REFRESH_URL, {'refresh': token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_cookie_is_used_when_body_is_empty(self):
        """Без поля refresh в теле токен берется из куки"""
        self.login(self.user)

        response = self.client.post(REFRESH_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_blank_body_token_falls_back_to_cookie(self):
        """Пустая строка в теле не мешает взять токен из куки"""
        self.login(self.user)

        response = self.client.post(REFRESH_URL, {'refresh': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_no_token_anywhere_gives_401(self):
        """Ни в теле, ни в куке — 401"""
        response = self.client.post(REFRESH_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_body_token_is_rejected(self):
        """Мусор в теле дает 401, а не молчаливый откат на куки"""
        self.login(self.user)

        response = self.client.post(
            REFRESH_URL, {'refresh': 'not-a-token'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
