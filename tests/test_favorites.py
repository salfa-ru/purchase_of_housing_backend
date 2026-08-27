from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from favorites.models import Favorite
from realty.models import Realty
from realty_values.models import RealtyType
from tests.factories import create_realty, create_user

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


class FavoriteRealtyTypeFilterTest(TestCase):
    """Фильтр избранного по типу недвижимости."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='typeuser',
            password='testpass123',
            email='type@test.com',
            phone_number='+79000000004',
        )
        self.client.force_authenticate(user=self.user)

        for _ in range(2):
            Favorite.objects.create(
                user=self.user, realty=create_realty(owner=self.user)
            )
        Favorite.objects.create(
            user=self.user,
            realty=create_realty(owner=self.user, realty_type_name='Апартаменты'),
        )

    def test_filter_by_russian_name(self):
        """Тест: фильтр по названию из справочника"""
        response = self.client.get('/api/favorites/?realty_type=Квартира')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_is_case_insensitive(self):
        """Тест: регистр значения не важен"""
        response = self.client.get('/api/favorites/?realty_type=квартира')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_english_alias(self):
        """Тест: английский алиас типа"""
        response = self.client.get('/api/favorites/?realty_type=apartment')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_several_types(self):
        """Тест: несколько типов через запятую"""
        response = self.client.get('/api/favorites/?realty_type=Квартира,Апартаменты')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_spaces_after_comma_are_allowed(self):
        """Тест: пробелы после запятой не мешают"""
        response = self.client.get('/api/favorites/?realty_type=Квартира, Апартаменты')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_unknown_type_returns_400(self):
        """Тест: неизвестный тип → 400"""
        response = self.client.get('/api/favorites/?realty_type=invalid')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_type', response.data)

    def test_unknown_type_in_list_returns_400(self):
        """Тест: невалидный элемент перечисления отклоняет весь запрос"""
        response = self.client.get('/api/favorites/?realty_type=Квартира,invalid')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_type', response.data)

    def test_empty_value_returns_400(self):
        """Тест: пустое значение → 400"""
        response = self.client.get('/api/favorites/?realty_type=')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_type', response.data)

    def test_without_param_returns_all(self):
        """Тест: без параметра отдаётся всё избранное"""
        response = self.client.get('/api/favorites/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)


class FavoriteCommercialAliasTest(TestCase):
    """Алиас commercial разворачивается во все коммерческие типы справочника."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('aliasowner')
        self.client.force_authenticate(user=self.user)

        self.office = RealtyType.objects.get(type='Офис')
        self.warehouse = RealtyType.objects.get(type='Склад')

        self.commercial = create_realty(self.user, realty_type=self.office)
        self.warehouse_realty = create_realty(self.user, realty_type=self.warehouse)
        self.residential = create_realty(self.user, realty_type_name='Квартира')

        for realty in (self.commercial, self.warehouse_realty, self.residential):
            Favorite.objects.create(user=self.user, realty=realty)

    def test_alias_returns_all_commercial(self):
        """Тест: ?realty_type=commercial отдаёт объекты всех коммерческих типов"""
        response = self.client.get('/api/favorites/?realty_type=commercial')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['realty']['id'] for item in response.data['results']}
        self.assertEqual(ids, {self.commercial.id, self.warehouse_realty.id})

    def test_alias_is_case_insensitive(self):
        """Тест: регистр в алиасе не важен"""
        response = self.client.get('/api/favorites/?realty_type=COMMERCIAL')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_alias_combines_with_plain_type(self):
        """Тест: алиас перечисляется вместе с обычным типом через запятую"""
        response = self.client.get('/api/favorites/?realty_type=commercial,Квартира')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
