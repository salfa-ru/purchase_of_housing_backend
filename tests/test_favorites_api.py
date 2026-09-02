"""Эндпоинты избранного: адреса, валидация фильтров, ответы."""

from django.test import TestCase
from rest_framework.test import APIClient

from favorites.models import Favorite
from tests.factories import create_realty, create_user

FAVORITES_URL = '/api/favorites/'
FAVORITES_LEGACY_CREATE_URL = '/api/favorites/create/'
FAVORITES_VIEWED_URL = '/api/favorites/viewed/'


class FavoriteEndpointsTest(TestCase):
    """Список, добавление, удаление и сброс счётчика."""

    def setUp(self):
        self.user = create_user('favuser')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.realty = create_realty(self.user)
        self.other_realty = create_realty(self.user)

    def test_post_to_collection_creates_favorite(self):
        """Тест: POST /favorites/ добавляет в избранное"""
        response = self.client.post(FAVORITES_URL, {'realty_id': self.realty.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['realty']['id'], self.realty.id)

    def test_legacy_create_url_still_works(self):
        """Тест: старый адрес /favorites/create/ продолжает работать"""
        response = self.client.post(
            FAVORITES_LEGACY_CREATE_URL, {'realty_id': self.realty.id}
        )
        self.assertEqual(response.status_code, 201)

    def test_legacy_create_url_rejects_get(self):
        """Тест: на старом адресе остался только POST"""
        self.assertEqual(self.client.get(FAVORITES_LEGACY_CREATE_URL).status_code, 405)

    def test_duplicate_returns_400(self):
        """Тест: повторное добавление → 400"""
        self.client.post(FAVORITES_URL, {'realty_id': self.realty.id})
        response = self.client.post(FAVORITES_URL, {'realty_id': self.realty.id})
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_realty_returns_404(self):
        """Тест: несуществующий realty_id → 404"""
        response = self.client.post(FAVORITES_URL, {'realty_id': 10**6})
        self.assertEqual(response.status_code, 404)

    def test_missing_realty_id_returns_400(self):
        """Тест: realty_id не передан → 400"""
        response = self.client.post(FAVORITES_URL, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('realty_id', response.json())

    def test_list_returns_unviewed_count(self):
        """Тест: список отдаёт счётчик непросмотренных"""
        self.client.post(FAVORITES_URL, {'realty_id': self.realty.id})
        payload = self.client.get(FAVORITES_URL).json()
        self.assertEqual(payload['unviewed_count'], 1)
        self.assertEqual(payload['count'], 1)

    def test_delete_own_favorite(self):
        """Тест: своё избранное удаляется"""
        favorite = Favorite.objects.create(user=self.user, realty=self.realty)
        response = self.client.delete(f'{FAVORITES_URL}{favorite.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Favorite.objects.filter(id=favorite.id).exists())

    def test_delete_someone_else_favorite_returns_404(self):
        """Тест: чужое избранное не удаляется"""
        stranger = create_user('stranger')
        favorite = Favorite.objects.create(user=stranger, realty=self.realty)
        response = self.client.delete(f'{FAVORITES_URL}{favorite.id}/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Favorite.objects.filter(id=favorite.id).exists())

    def test_viewed_returns_200_with_body(self):
        """Тест: сброс счётчика отдаёт 200 и тело ответа"""
        Favorite.objects.create(user=self.user, realty=self.realty)
        Favorite.objects.create(user=self.user, realty=self.other_realty)

        response = self.client.post(FAVORITES_VIEWED_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'viewed', 'update_count': 2})
        self.assertFalse(
            Favorite.objects.filter(user=self.user, is_viewed=False).exists()
        )

    def test_anonymous_gets_401(self):
        """Тест: избранное закрыто от анонимов"""
        anonymous = APIClient()
        self.assertEqual(anonymous.get(FAVORITES_URL).status_code, 401)


class FavoriteFilterValidationTest(TestCase):
    """Недопустимые значения фильтров дают 400, а не 500 и не тихую выдачу."""

    def setUp(self):
        self.user = create_user('filteruser')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.realty = create_realty(self.user)
        Favorite.objects.create(user=self.user, realty=self.realty)

    def test_unknown_ordering_returns_400(self):
        """Тест: произвольное значение ordering → 400"""
        response = self.client.get(FAVORITES_URL, {'ordering': 'realty__price'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('ordering', response.json())

    def test_known_ordering_values_are_accepted(self):
        """Тест: added_at и -added_at принимаются"""
        for value in ('added_at', '-added_at'):
            with self.subTest(ordering=value):
                response = self.client.get(FAVORITES_URL, {'ordering': value})
                self.assertEqual(response.status_code, 200)

    def test_default_ordering_is_newest_first(self):
        """Тест: по умолчанию сначала новые"""
        second = Favorite.objects.create(
            user=self.user, realty=create_realty(self.user)
        )
        results = self.client.get(FAVORITES_URL).json()['results']
        self.assertEqual(results[0]['id'], second.id)

    def test_unknown_trade_type_returns_400(self):
        """Тест: неизвестный trade_type → 400, а не вся выдача"""
        response = self.client.get(FAVORITES_URL, {'trade_type': 'barter'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('trade_type', response.json())

    def test_trade_type_is_case_insensitive(self):
        """Тест: регистр trade_type не важен"""
        response = self.client.get(FAVORITES_URL, {'trade_type': 'SALE'})
        self.assertEqual(response.status_code, 200)

    def test_unknown_is_commercial_returns_400(self):
        """Тест: is_commercial принимает только true/false"""
        response = self.client.get(FAVORITES_URL, {'is_commercial': 'yes'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('is_commercial', response.json())

    def test_known_is_commercial_values_are_accepted(self):
        """Тест: true и false принимаются"""
        for value in ('true', 'FALSE'):
            with self.subTest(is_commercial=value):
                response = self.client.get(FAVORITES_URL, {'is_commercial': value})
                self.assertEqual(response.status_code, 200)
