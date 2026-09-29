"""Инфраструктура пуш-уведомлений: токены устройств и отправка."""

import sys
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from notifications.models import DeviceToken
from notifications.push import send_push
from tests.factories import create_user

DEVICES_URL = '/api/notifications/devices/'


class DeviceTokenRegistrationTest(TestCase):
    """Регистрация и удаление токена устройства."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('pushowner')
        self.other_user = create_user('pushother')
        self.client.force_authenticate(self.user)

    def register(self, token='token-abc', platform='android'):
        return self.client.post(
            DEVICES_URL, {'token': token, 'platform': platform}, format='json'
        )

    def test_token_is_registered(self):
        """Токен сохраняется за текущим пользователем"""
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        device = DeviceToken.objects.get(token='token-abc')
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.platform, 'android')

    def test_repeated_registration_does_not_duplicate(self):
        """Повторная регистрация того же токена не плодит записи"""
        self.register()
        self.register(platform='web')

        self.assertEqual(DeviceToken.objects.filter(token='token-abc').count(), 1)
        self.assertEqual(DeviceToken.objects.get(token='token-abc').platform, 'web')

    def test_token_moves_to_new_owner(self):
        """Тот же токен на другом аккаунте переезжает к новому владельцу"""
        self.register()

        self.client.force_authenticate(self.other_user)
        self.register()

        device = DeviceToken.objects.get(token='token-abc')
        self.assertEqual(device.user, self.other_user)

    def test_unknown_platform_is_rejected(self):
        """Платформа вне списка не принимается"""
        response = self.register(platform='symbian')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_cannot_register(self):
        """Без авторизации токен зарегистрировать нельзя"""
        self.client.force_authenticate(None)

        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_own_token_is_deleted(self):
        """Свой токен удаляется"""
        self.register()

        response = self.client.delete(f'{DEVICES_URL}token-abc/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DeviceToken.objects.filter(token='token-abc').exists())

    def test_foreign_token_is_not_deleted(self):
        """Чужой токен удалить нельзя"""
        self.register()
        self.client.force_authenticate(self.other_user)

        response = self.client.delete(f'{DEVICES_URL}token-abc/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(DeviceToken.objects.filter(token='token-abc').exists())


class SendPushTest(TestCase):
    """Отправка пуша при выключенном Firebase."""

    def setUp(self):
        self.user = create_user('pushreceiver')

    @override_settings(FIREBASE_ENABLED=False)
    def test_disabled_firebase_only_logs(self):
        """С выключенным флагом пуш не уходит, но пишется в лог"""
        DeviceToken.objects.create(
            user=self.user, token='token-log', platform='android'
        )

        with self.assertLogs('notifications.push', level='INFO') as logs:
            sent = send_push(self.user, 'Заголовок', 'Текст')

        self.assertEqual(sent, 0)
        self.assertIn('push (заглушка)', '\n'.join(logs.output))

    @override_settings(FIREBASE_ENABLED=False)
    def test_user_without_devices(self):
        """Без зарегистрированных устройств отправка тихо пропускается"""
        with self.assertLogs('notifications.push', level='DEBUG') as logs:
            sent = send_push(self.user, 'Заголовок')

        self.assertEqual(sent, 0)
        self.assertIn('нет устройств', '\n'.join(logs.output))

    @override_settings(FIREBASE_ENABLED=True)
    def test_enabled_firebase_sends_to_all_devices(self):
        """С включенным флагом отправка уходит на все токены пользователя"""
        DeviceToken.objects.create(user=self.user, token='token-one', platform='ios')
        DeviceToken.objects.create(user=self.user, token='token-two', platform='web')

        with patch('notifications.push._send_via_fcm', return_value=2) as send:
            sent = send_push(self.user, 'Заголовок', 'Текст')

        self.assertEqual(sent, 2)
        tokens = send.call_args.args[0]
        self.assertCountEqual(tokens, ['token-one', 'token-two'])

    @override_settings(FIREBASE_ENABLED=True)
    def test_missing_package_does_not_break(self):
        """Если пакет firebase-admin не установлен, отправка не падает"""
        DeviceToken.objects.create(user=self.user, token='token-fcm', platform='ios')

        # Пакет в окружении есть, поэтому отсутствие имитируем подменой импорта
        with patch.dict(sys.modules, {'firebase_admin': None}):
            with self.assertLogs('notifications.push', level='WARNING') as logs:
                sent = send_push(self.user, 'Заголовок', 'Текст')

        self.assertEqual(sent, 0)
        self.assertIn('firebase-admin не установлен', '\n'.join(logs.output))

    @override_settings(FIREBASE_ENABLED=True)
    def test_fcm_error_does_not_break(self):
        """Ошибка обращения к FCM не выходит наружу"""
        DeviceToken.objects.create(user=self.user, token='token-fcm', platform='ios')

        with patch(
            'notifications.push._send_via_fcm', side_effect=RuntimeError('FCM упал')
        ):
            with self.assertLogs('notifications.push', level='ERROR') as logs:
                sent = send_push(self.user, 'Заголовок')

        self.assertEqual(sent, 0)
        self.assertIn('push не отправлен', '\n'.join(logs.output))
