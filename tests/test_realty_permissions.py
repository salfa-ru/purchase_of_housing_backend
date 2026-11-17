"""Чужое объявление нельзя ни править, ни снимать с публикации: ответ 403,
а не ошибка в поле."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from realty.models import Realty
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user

STATUS_URL = '/api/realty/{}/status/'
SALE_URL = '/api/realty/sales/{}/'
RENT_URL = '/api/realty/rents/{}/'


class RealtyOwnerPermissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user('permowner')
        cls.stranger = create_user('permstranger')
        cls.sale = create_realty(cls.owner, trade_type='sale')
        cls.rent = create_realty(cls.owner, trade_type='rent')
        cls.active, _ = RealtyAdvStatus.objects.get_or_create(status='Активно')
        cls.archived, _ = RealtyAdvStatus.objects.get_or_create(status='В архиве')

    def setUp(self):
        self.client = APIClient()

    def as_stranger(self):
        self.client.force_authenticate(user=self.stranger)

    def as_owner(self):
        self.client.force_authenticate(user=self.owner)

    def activate(self, realty):
        Realty.objects.filter(pk=realty.pk).update(realty_status=self.active)

    def patch_description(self, url, realty_id):
        return self.client.patch(
            url.format(realty_id), {'description': 'Чужая правка'}, format='json'
        )

    def test_stranger_cannot_edit_sale(self):
        """Чужое объявление о продаже не правится"""
        self.as_stranger()
        response = self.patch_description(SALE_URL, self.sale.sale_profile.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.sale.refresh_from_db()
        self.assertNotEqual(self.sale.description, 'Чужая правка')

    def test_stranger_cannot_edit_rent(self):
        """Чужое объявление об аренде не правится"""
        self.as_stranger()
        response = self.patch_description(RENT_URL, self.rent.rent_profile.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_edits_own_sale(self):
        """Своё объявление владелец правит как раньше"""
        self.as_owner()
        response = self.patch_description(SALE_URL, self.sale.sale_profile.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.description, 'Чужая правка')

    def test_stranger_cannot_change_status(self):
        """Чужой статус не меняется: 403, а не ошибка в поле"""
        self.activate(self.sale)
        self.as_stranger()
        response = self.client.patch(
            STATUS_URL.format(self.sale.id),
            {'realty_status': self.archived.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.json())
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.realty_status_id, self.active.id)

    def test_owner_archives_own_realty(self):
        """Своё объявление владелец убирает в архив"""
        self.activate(self.sale)
        self.as_owner()
        response = self.client.patch(
            STATUS_URL.format(self.sale.id),
            {'realty_status': self.archived.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.realty_status_id, self.archived.id)

    def test_owner_cannot_make_forbidden_transition(self):
        """Запрещённый переход статуса — 400 с объяснением"""
        self.activate(self.rent)
        self.as_owner()
        response = self.client.patch(
            STATUS_URL.format(self.rent.id),
            {'realty_status': self.active.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_status', response.json())

    def test_anonymous_cannot_change_status(self):
        """Гость статус не меняет"""
        self.activate(self.sale)
        response = self.client.patch(
            STATUS_URL.format(self.sale.id),
            {'realty_status': self.archived.id},
            format='json',
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
