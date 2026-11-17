"""Чужое объявление видно по прямой ссылке, только пока оно опубликовано,
и контакты владельца — тоже."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty.models import Realty
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user

DETAIL_URL = '/api/realty/{}/'
OWNER_URL = '/api/realty/{}/owner/'
CONTACTS_URL = '/api/realty/{}/contacts/'


class RealtyVisibilityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user('visibilityowner')
        cls.stranger = create_user('visibilitystranger')
        cls.active = create_realty(cls.owner, trade_type='sale')
        cls.archived = create_realty(cls.owner, trade_type='sale')

        active_status, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        archived_status, _ = RealtyAdvStatus.objects.get_or_create(status='В архиве')
        Realty.objects.filter(pk=cls.active.pk).update(realty_status=active_status)
        Realty.objects.filter(pk=cls.archived.pk).update(realty_status=archived_status)

    def setUp(self):
        self.client = APIClient()

    # --- Карточка объявления ---

    def test_stranger_sees_active_realty(self):
        """Опубликованное объявление открывается у всех"""
        response = self.client.get(DETAIL_URL.format(self.active.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stranger_does_not_see_archived_realty(self):
        """Чужое архивное объявление по прямой ссылке — 404"""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(DETAIL_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_does_not_see_archived_realty(self):
        """Гостю архивное объявление тоже не показывается"""
        response = self.client.get(DETAIL_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_sees_own_archived_realty(self):
        """Своё архивное объявление владелец открывает"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(DETAIL_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Контакты владельца ---

    def test_owner_data_requires_authentication(self):
        """Телефон владельца не отдаётся без авторизации"""
        response = self.client.get(OWNER_URL.format(self.active.id))
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_owner_data_is_given_for_active_realty(self):
        """По опубликованному объявлению телефон виден авторизованному"""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(OWNER_URL.format(self.active.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('phone_number', response.json()['owner'])

    def test_owner_data_is_hidden_for_archived_realty(self):
        """По чужому архивному объявлению телефон не отдаётся"""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(OWNER_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_contacts_are_hidden_for_archived_realty(self):
        """Контакты по чужому архивному объявлению тоже закрыты"""
        self.client.force_authenticate(user=self.stranger)
        response = self.client.get(CONTACTS_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_sees_contacts_of_own_archived_realty(self):
        """Своё архивное объявление владельцу доступно целиком"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(CONTACTS_URL.format(self.archived.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
