"""GET /api/realty/batch/?ids=1,2,3 — выборка объявлений для сравнения."""

from django.test import TestCase
from rest_framework.test import APIClient

from config import constants
from tests.factories import create_realty, create_user

BATCH_URL = '/api/realty/batch/'


class RealtyBatchViewTest(TestCase):
    """Порядок, видимость и разбор параметра ids."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('batchowner')
        cls.first = create_realty(cls.user)
        cls.second = create_realty(cls.user)
        cls.third = create_realty(cls.user)

    def setUp(self):
        self.client = APIClient()

    def ids_from(self, response):
        return [item['id'] for item in response.json()]

    def test_order_follows_request(self):
        """Тест: объявления возвращаются в порядке запрошенных ID"""
        ids = f'{self.third.id},{self.first.id},{self.second.id}'
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.ids_from(response), [self.third.id, self.first.id, self.second.id]
        )

    def test_duplicates_collapse(self):
        """Тест: повторяющийся ID не дублируется в ответе"""
        ids = f'{self.first.id},{self.first.id},{self.second.id}'
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(self.ids_from(response), [self.first.id, self.second.id])

    def test_missing_id_is_skipped(self):
        """Тест: несуществующий ID просто выпадает из выдачи"""
        ids = f'{self.first.id},{10**6}'
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(self.ids_from(response), [self.first.id])

    def test_deleted_realty_is_hidden(self):
        """Тест: удалённое объявление не отдаётся"""
        self.second.is_deleted = True
        self.second.save()

        ids = f'{self.first.id},{self.second.id}'
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(self.ids_from(response), [self.first.id])

    def test_realty_of_deleted_owner_is_hidden(self):
        """Тест: объявление удалённого владельца не отдаётся"""
        owner = create_user('deletedowner')
        realty = create_realty(owner)
        owner.is_deleted = True
        owner.save()

        response = self.client.get(BATCH_URL, {'ids': f'{self.first.id},{realty.id}'})
        self.assertEqual(self.ids_from(response), [self.first.id])

    def test_too_many_ids_returns_400(self):
        """Тест: слишком длинный список ID → 400"""
        ids = ','.join(str(number) for number in range(constants.BATCH_IDS_MAX + 1))
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(response.status_code, 400)

    def test_max_ids_is_accepted(self):
        """Тест: список ровно на предел принимается"""
        ids = ','.join(str(number) for number in range(constants.BATCH_IDS_MAX))
        response = self.client.get(BATCH_URL, {'ids': ids})
        self.assertEqual(response.status_code, 200)

    def test_missing_ids_returns_400(self):
        """Тест: без параметра ids → 400"""
        self.assertEqual(self.client.get(BATCH_URL).status_code, 400)

    def test_non_numeric_ids_returns_400(self):
        """Тест: нечисловой ID → 400"""
        response = self.client.get(BATCH_URL, {'ids': '1,abc'})
        self.assertEqual(response.status_code, 400)
