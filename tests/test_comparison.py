"""Модуль сравнения: два списка на сервере — продажа и аренда, в каждом не больше
3 объявлений, удалённые и архивные объявления остаются в списке с пометкой."""

from django.core.management.color import no_style
from django.db import connection
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from comparison.views import LIMIT_REACHED, NO_TRADE_TYPE
from config import constants
from realty.models import Realty
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user

COMPARISON_URL = '/api/comparison/'


def delete_url(realty_id):
    return f'{COMPARISON_URL}{realty_id}/'


def create_statuses():
    """Статусы с теми id, на которые опирается код. Счётчик id сбрасывается,
    чтобы последующие автоматические вставки не наткнулись на занятый id."""
    active, _ = RealtyAdvStatus.objects.get_or_create(
        id=constants.STATUS_ACTIVE_ID, defaults={'status': 'Опубликовано'}
    )
    archived, _ = RealtyAdvStatus.objects.get_or_create(
        id=constants.STATUS_ARCHIVED_ID, defaults={'status': 'В архиве'}
    )
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [RealtyAdvStatus]):
            cursor.execute(sql)
    return active, archived


class ComparisonTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active, cls.archived = create_statuses()
        cls.user = create_user('comparer')
        cls.owner = create_user('realtyowner')
        cls.realties = [create_realty(cls.owner, trade_type='sale') for _ in range(4)]
        cls.rents = [create_realty(cls.owner, trade_type='rent') for _ in range(4)]

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def add(self, realty):
        return self.client.post(COMPARISON_URL, {'realty_id': realty.id}, format='json')

    def listed(self):
        return self.client.get(COMPARISON_URL).json()

    def sales(self):
        return self.listed()['sale']

    def listed_ids(self, trade_type='sale'):
        return [item['realty']['id'] for item in self.listed()[trade_type]['results']]

    def archive(self, realty):
        Realty.objects.filter(pk=realty.pk).update(realty_status=self.archived)

    def test_empty_list(self):
        """Пустые списки продажи и аренды сообщают лимит"""
        empty = {'count': 0, 'results': []}
        self.assertEqual(self.listed(), {'max_count': 3, 'sale': empty, 'rent': empty})

    def test_added_realty_comes_with_characteristics(self):
        """Добавленное объявление отдаётся с характеристиками"""
        response = self.add(self.realties[0])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        item = self.sales()['results'][0]
        self.assertTrue(item['is_available'])
        self.assertEqual(item['realty']['id'], self.realties[0].id)
        self.assertIn('price', item['realty'])
        self.assertIn('about_apartment', item['realty'])

    def test_order_follows_addition(self):
        """Колонки идут в порядке добавления"""
        for realty in (self.realties[2], self.realties[0], self.realties[1]):
            self.add(realty)

        self.assertEqual(
            self.listed_ids(),
            [self.realties[2].id, self.realties[0].id, self.realties[1].id],
        )

    def test_duplicate_is_rejected(self):
        """Повторное добавление → 400"""
        self.add(self.realties[0])
        response = self.add(self.realties[0])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.sales()['count'], 1)

    def test_fourth_realty_is_rejected(self):
        """Четвёртое объявление → 400 с понятным текстом"""
        for realty in self.realties[:3]:
            self.assertEqual(self.add(realty).status_code, status.HTTP_201_CREATED)

        response = self.add(self.realties[3])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], LIMIT_REACHED)
        self.assertEqual(self.sales()['count'], 3)

    def test_missing_realty_returns_404(self):
        """Несуществующее объявление → 404"""
        response = self.client.post(COMPARISON_URL, {'realty_id': 10**6}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleted_realty_cannot_be_added(self):
        """Удалённое объявление добавить нельзя → 404"""
        Realty.objects.filter(pk=self.realties[0].pk).update(is_deleted=True)
        self.assertEqual(self.add(self.realties[0]).status_code, 404)

    def test_realty_of_deleted_owner_cannot_be_added(self):
        """Объявление удалённого владельца добавить нельзя → 404"""
        owner = create_user('goneowner')
        realty = create_realty(owner, trade_type='sale')
        owner.is_deleted = True
        owner.save()

        self.assertEqual(self.add(realty).status_code, 404)

    def test_archived_realty_cannot_be_added(self):
        """Архивное объявление добавить нельзя → 400"""
        self.archive(self.realties[0])
        self.assertEqual(self.add(self.realties[0]).status_code, 400)

    def test_invalid_realty_id_returns_400(self):
        """Нечисловой realty_id → 400"""
        response = self.client.post(COMPARISON_URL, {'realty_id': 'abc'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_id', response.data)

    def test_archived_after_adding_stays_marked(self):
        """Ушедшее в архив объявление остаётся в списке с пометкой"""
        self.add(self.realties[0])
        self.archive(self.realties[0])

        item = self.sales()['results'][0]
        self.assertFalse(item['is_available'])
        self.assertEqual(item['realty']['realty_status'], constants.STATUS_ARCHIVED_ID)

    def test_deleted_after_adding_stays_without_data(self):
        """Удалённое объявление остаётся в списке, но без своих данных"""
        self.add(self.realties[0])
        Realty.objects.filter(pk=self.realties[0].pk).update(is_deleted=True)

        item = self.sales()['results'][0]
        self.assertFalse(item['is_available'])
        self.assertEqual(item['realty_id'], self.realties[0].id)
        self.assertIsNone(item['realty'])

    def test_realty_of_deleted_owner_stays_without_data(self):
        """Объявление удалённого владельца отдаётся без данных и имени"""
        owner = create_user('leavingowner', first_name='Ушедший')
        realty = create_realty(owner, trade_type='sale')
        self.add(realty)
        owner.soft_delete()

        item = self.sales()['results'][0]
        self.assertFalse(item['is_available'])
        self.assertIsNone(item['realty'])
        self.assertEqual(item['trade_type'], 'sale')
        self.assertNotIn('Ушедший', str(item))

    def test_deleted_realty_can_be_removed_by_realty_id(self):
        """Удалённое объявление убирается по realty_id и освобождает место"""
        self.add(self.realties[0])
        Realty.objects.filter(pk=self.realties[0].pk).update(is_deleted=True)

        realty_id = self.sales()['results'][0]['realty_id']
        response = self.client.delete(delete_url(realty_id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.sales()['count'], 0)

    def test_archived_realty_keeps_data(self):
        """Архивное объявление отдаётся с данными, как и в карточке"""
        self.add(self.realties[0])
        self.archive(self.realties[0])

        self.assertIsNotNone(self.sales()['results'][0]['realty'])

    def test_unavailable_realty_still_counts_toward_limit(self):
        """Недоступное объявление занимает место, пока его не уберут"""
        for realty in self.realties[:3]:
            self.add(realty)
        self.archive(self.realties[0])

        self.assertEqual(self.add(self.realties[3]).status_code, 400)

        self.client.delete(delete_url(self.realties[0].id))
        self.assertEqual(self.add(self.realties[3]).status_code, 201)

    def test_delete_by_realty_id(self):
        """Удаление по ID объявления → 204, объявление уходит из списка"""
        self.add(self.realties[0])
        self.add(self.realties[1])

        response = self.client.delete(delete_url(self.realties[0].id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.listed_ids(), [self.realties[1].id])

    def test_delete_missing_returns_404(self):
        """Удаление объявления, которого нет в сравнении → 404"""
        response = self.client.delete(delete_url(self.realties[0].id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_lists_are_per_user(self):
        """У каждого пользователя свой список"""
        self.add(self.realties[0])

        other = APIClient()
        other.force_authenticate(user=create_user('othercomparer'))

        self.assertEqual(other.get(COMPARISON_URL).json()['sale']['count'], 0)
        self.assertEqual(other.delete(delete_url(self.realties[0].id)).status_code, 404)
        self.assertEqual(self.sales()['count'], 1)

    def test_realty_goes_to_list_of_its_trade_type(self):
        """Продажа попадает в список продажи, аренда — в список аренды"""
        sale = self.add(self.realties[0])
        rent = self.add(self.rents[0])

        self.assertEqual(sale.data['trade_type'], 'sale')
        self.assertEqual(rent.data['trade_type'], 'rent')
        self.assertEqual(self.listed_ids('sale'), [self.realties[0].id])
        self.assertEqual(self.listed_ids('rent'), [self.rents[0].id])

    def test_limit_is_per_list(self):
        """Лимит в 3 объявления считается отдельно для продажи и аренды"""
        for realty in self.realties[:3] + self.rents[:3]:
            self.assertEqual(self.add(realty).status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.add(self.realties[3]).status_code, 400)
        self.assertEqual(self.add(self.rents[3]).status_code, 400)

        listed = self.listed()
        self.assertEqual(listed['sale']['count'], 3)
        self.assertEqual(listed['rent']['count'], 3)

    def test_full_sale_list_does_not_block_rent(self):
        """Полный список продажи не мешает добавить аренду"""
        for realty in self.realties[:3]:
            self.add(realty)

        self.assertEqual(self.add(self.rents[0]).status_code, 201)

    def test_removing_frees_place_only_in_its_list(self):
        """Удаление аренды освобождает место только в списке аренды"""
        for realty in self.realties[:3] + self.rents[:3]:
            self.add(realty)

        self.client.delete(delete_url(self.rents[0].id))

        self.assertEqual(self.add(self.realties[3]).status_code, 400)
        self.assertEqual(self.add(self.rents[3]).status_code, 201)

    def test_realty_without_trade_type_is_rejected(self):
        """Объявление без продажи и аренды добавить нельзя → 400"""
        realty = create_realty(self.owner)

        response = self.add(realty)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], NO_TRADE_TYPE)

    def test_anonymous_gets_401(self):
        """Без авторизации → 401"""
        anonymous = APIClient()
        self.assertEqual(anonymous.get(COMPARISON_URL).status_code, 401)
        self.assertEqual(
            anonymous.post(COMPARISON_URL, {'realty_id': 1}).status_code, 401
        )
