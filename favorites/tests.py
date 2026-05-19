from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from realty.models import Realty

User = get_user_model()


class FavoriteCreateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаём тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com',
            phone_number='1234567890',
        )
        self.client.force_authenticate(user=self.user)

        # Берём существующее объявление из БД (id=1)
        # Если его нет — тесты пропустим
        self.realty_id = 1
        self.realty_exists = Realty.objects.filter(id=self.realty_id).exists()

    def test_duplicate_favorite_returns_400(self):
        """Тест: дубликат → 400"""
        if not self.realty_exists:
            self.skipTest("Realty with id=1 doesn't exist")

        # Первое добавление
        response1 = self.client.post(
            '/api/favorites/create/', {'realty_id': self.realty_id}
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Второе добавление (дубликат) — должно вернуть 400
        response2 = self.client.post(
            '/api/favorites/create/', {'realty_id': self.realty_id}
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_realty_returns_404(self):
        """Тест: несуществующий realty_id → 404"""
        response = self.client.post('/api/favorites/create/', {'realty_id': 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_realty_id_returns_400(self):
        """Тест: realty_id не передан → 400"""
        response = self.client.post('/api/favorites/create/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_id', response.data)
