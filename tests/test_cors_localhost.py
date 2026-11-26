"""CORS: локальный фронт на любом порту пускается, чужие адреса — нет."""

from django.test import TestCase

PREFLIGHT_URL = '/api/auth/token-auth/'


class LocalhostCorsTest(TestCase):
    """Preflight-запросы с разных origin."""

    def preflight(self, origin):
        return self.client.options(
            PREFLIGHT_URL,
            HTTP_ORIGIN=origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type',
        )

    def test_localhost_on_any_port_is_allowed(self):
        """Тест: localhost и 127.0.0.1 на любом порту получают разрешение"""
        for origin in (
            'http://localhost:3000',
            'http://localhost:5173',
            'https://localhost:8080',
            'http://127.0.0.1:4200',
            'http://localhost',
        ):
            with self.subTest(origin=origin):
                response = self.preflight(origin)
                self.assertEqual(response.get('Access-Control-Allow-Origin'), origin)
                self.assertEqual(
                    response.get('Access-Control-Allow-Credentials'), 'true'
                )

    def test_foreign_origin_is_not_allowed(self):
        """Тест: посторонние адреса и подделки под localhost не пускаются"""
        for origin in (
            'https://example.com',
            'http://localhost.evil.com',
            'http://evil-localhost:3000',
            'http://127.0.0.1.evil.com',
        ):
            with self.subTest(origin=origin):
                response = self.preflight(origin)
                self.assertIsNone(response.get('Access-Control-Allow-Origin'))
