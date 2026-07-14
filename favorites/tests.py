from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from favorites.models import Favorite
from realty.models import Realty
from realty_addresses.models import Address
from realty_specificities.models import AboutApartment
from realty_values.models import (
    CommunicationMethod,
    RealtyAdvStatus,
    RealtyType,
    RoomsNumber,
    TradeParticipant,
)

User = get_user_model()


def create_realty(owner, **kwargs):
    """Создаёт объявление со всеми обязательными связями."""
    realty_type, _ = RealtyType.objects.get_or_create(
        type='Квартира', defaults={'is_commercial': False}
    )
    owner_type, _ = TradeParticipant.objects.get_or_create(participant='Собственник')
    communication_method, _ = CommunicationMethod.objects.get_or_create(method='Звонок')
    realty_status, _ = RealtyAdvStatus.objects.get_or_create(status='Опубликовано')
    rooms_number, _ = RoomsNumber.objects.get_or_create(number_of_rooms='2')

    address = Address.objects.create(house_number='1', latitude=55.7, longitude=37.6)
    about_apartment = AboutApartment.objects.create(
        number_of_rooms=rooms_number, area=50.0, floor=2, floors_number=9
    )

    return Realty.objects.create(
        owner=owner,
        realty_type=realty_type,
        address=address,
        about_apartment=about_apartment,
        description='Тестовое объявление',
        price=1000000,
        owner_type=owner_type,
        communication_method=communication_method,
        realty_status=realty_status,
        **kwargs,
    )


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


class FavoritePaginationTest(TestCase):
    """Пагинация списка избранного."""

    TOTAL = 9
    PAGE_SIZE = constants.FAVORITES_PAGESIZE_DEFAULT

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='pageuser',
            password='testpass123',
            email='page@test.com',
            phone_number='+79000000003',
        )
        self.client.force_authenticate(user=self.user)

        for _ in range(self.TOTAL):
            Favorite.objects.create(
                user=self.user, realty=create_realty(owner=self.user)
            )

    def test_first_page(self):
        """Тест: первая страница — PAGE_SIZE записей и данные для навигации"""
        response = self.client.get('/api/favorites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), self.PAGE_SIZE)
        self.assertEqual(response.data['count'], self.TOTAL)
        self.assertEqual(response.data['page_size'], self.PAGE_SIZE)
        self.assertEqual(response.data['pages_total'], 3)
        self.assertEqual(response.data['current_page'], 1)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_last_page(self):
        """Тест: последняя страница — остаток записей, next пустой"""
        response = self.client.get('/api/favorites/?page=3')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), self.TOTAL % self.PAGE_SIZE)
        self.assertEqual(response.data['current_page'], 3)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])

    def test_unviewed_count_counts_all_favorites(self):
        """Тест: unviewed_count считается по всему избранному, а не по странице"""
        viewed = Favorite.objects.filter(user=self.user)[:2]
        Favorite.objects.filter(id__in=[f.id for f in viewed]).update(is_viewed=True)

        response = self.client.get('/api/favorites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unviewed_count'], self.TOTAL - 2)
        self.assertEqual(len(response.data['results']), self.PAGE_SIZE)

    def test_nonexistent_page_returns_404(self):
        """Тест: несуществующая страница → 404"""
        response = self.client.get('/api/favorites/?page=99')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination_works_with_filters(self):
        """Тест: фильтр и пагинация работают вместе"""
        response = self.client.get('/api/favorites/?is_commercial=false')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.TOTAL)
        self.assertEqual(len(response.data['results']), self.PAGE_SIZE)
