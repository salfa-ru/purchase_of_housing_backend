from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

DOCS_URLS = ('/schema/', '/swagger/', '/redoc/')


class DocsAccessTest(TestCase):
    """Документация доступна только администраторам (is_staff=True)."""

    def setUp(self):
        self.client = APIClient()

        self.user_password = 'testpass123'
        self.user = User.objects.create_user(
            username='testuser',
            password=self.user_password,
            email='test@test.com',
            phone_number='+79000000001',
        )
        self.admin = User.objects.create_user(
            username='testadmin',
            password=self.user_password,
            email='admin@test.com',
            phone_number='+79000000002',
            is_staff=True,
        )

    def test_anonymous_gets_403(self):
        """Тест: без авторизации → 403"""
        for url in DOCS_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_gets_403(self):
        """Тест: обычный пользователь → 403"""
        self.client.login(username=self.user.username, password=self.user_password)

        for url in DOCS_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_gets_200(self):
        """Тест: админ (is_staff=True) → 200"""
        self.client.login(username=self.admin.username, password=self.user_password)

        for url in DOCS_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
