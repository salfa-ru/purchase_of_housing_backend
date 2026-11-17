"""Целостность данных: создание идёт одной транзакцией, координаты
проверяются, удалённое объявление в избранное не попадает, а команда ревизии
находит и чинит записи, которые через API появиться не могли."""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from realty.models import Realty
from realty_addresses.models import City, District, Street, Zone
from realty_values.models import (
    CommunicationMethod,
    RealtyType,
    RoomsNumber,
    TradeParticipant,
)
from tests.factories import create_realty, create_user

SALES_URL = '/api/realty/sales/'
RENTS_URL = '/api/realty/rents/'
FAVORITES_URL = '/api/favorites/'


class RealtyCreateIntegrityTest(TestCase):
    """Если создание сорвалось, в базе не остаётся объявления без сделки."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('integrityseller')
        cls.flat, _ = RealtyType.objects.get_or_create(
            type='Квартира', defaults={'is_commercial': False}
        )
        cls.rooms, _ = RoomsNumber.objects.get_or_create(number_of_rooms='2')
        cls.owner_type, _ = TradeParticipant.objects.get_or_create(
            participant='Собственник'
        )
        cls.method, _ = CommunicationMethod.objects.get_or_create(method='Звонок')
        cls.city = City.objects.create(name='Москва')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def payload(self, **overrides):
        payload = {
            'realty_type': self.flat.id,
            'address': {
                'house_number': '1',
                'latitude': 55.75,
                'longitude': 37.6,
                'street': {'name': 'Тверская', 'city': self.city.id},
            },
            'about_apartment': {
                'area': 60,
                'floor': 1,
                'floors_number': 5,
                'number_of_rooms': self.rooms.id,
            },
            'description': 'Квартира',
            'price': 100000,
            'owner_type': self.owner_type.id,
            'communication_method': self.method.id,
        }
        payload.update(overrides)
        return payload

    def test_sale_creates_realty_with_trade(self):
        """Удачное создание даёт объявление вместе с продажей"""
        response = self.client.post(SALES_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        realty = Realty.objects.get(id=response.data['id'])
        self.assertTrue(hasattr(realty, 'sale_profile'))

    def test_failed_sale_leaves_nothing_behind(self):
        """Если продажа не записалась, объявление не остаётся в базе.
        Так и появилось объявление без типа сделки: раньше транзакции не было."""
        before = Realty.objects.count()
        with patch(
            'realty.models.Sale.objects.create',
            side_effect=RuntimeError('база недоступна'),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(SALES_URL, self.payload(), format='json')

        self.assertEqual(Realty.objects.count(), before)

    def test_failed_rent_leaves_nothing_behind(self):
        """То же для аренды"""
        before = Realty.objects.count()
        with patch(
            'realty.models.Rent.objects.create',
            side_effect=RuntimeError('база недоступна'),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(RENTS_URL, {'realty': self.payload()}, format='json')

        self.assertEqual(Realty.objects.count(), before)

    def test_broken_nested_block_is_rejected(self):
        """Негодные условия сдачи — 400 и ничего не создано"""
        before = Realty.objects.count()
        payload = {
            'realty': self.payload(),
            'lease_payments': {'deposit': 'не число'},
        }
        response = self.client.post(RENTS_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Realty.objects.count(), before)

    # --- Публикатор ---

    def test_tenant_cannot_be_a_publisher(self):
        """Публикатором может быть только собственник или агент (ФТ-1.6.2)"""
        tenant, _ = TradeParticipant.objects.get_or_create(participant='Арендатор')
        before = Realty.objects.count()

        response = self.client.post(
            SALES_URL, self.payload(owner_type=tenant.id), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('owner_type', response.json())
        self.assertEqual(Realty.objects.count(), before)

    def test_agent_can_be_a_publisher(self):
        """Агент объявление разместить может"""
        agent, _ = TradeParticipant.objects.get_or_create(participant='Агент')

        response = self.client.post(
            SALES_URL, self.payload(owner_type=agent.id), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_coordinates_outside_the_globe_are_rejected(self):
        """Координаты вне допустимого диапазона — 400"""
        payload = self.payload()
        payload['address']['latitude'] = 155.0
        response = self.client.post(SALES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.json().get('address', {}))


class FavoriteDeletedRealtyTest(TestCase):
    """Удалённое объявление в избранное не кладётся."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('favintegrity')
        owner = create_user('favintegrityowner')
        cls.realty = create_realty(owner, trade_type='sale')
        cls.deleted = create_realty(owner, trade_type='sale')
        Realty.objects.filter(pk=cls.deleted.pk).update(is_deleted=True)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def add(self, realty):
        return self.client.post(FAVORITES_URL, {'realty_id': realty.id}, format='json')

    def test_deleted_realty_is_not_added(self):
        """Удалённое объявление — 404"""
        self.assertEqual(self.add(self.deleted).status_code, status.HTTP_404_NOT_FOUND)

    def test_available_realty_is_added(self):
        """Обычное объявление добавляется как раньше"""
        self.assertEqual(self.add(self.realty).status_code, status.HTTP_201_CREATED)


class AuditRealtyCommandTest(TestCase):
    """Команда ревизии находит битые записи и чинит однозначные случаи."""

    @classmethod
    def setUpTestData(cls):
        owner = create_user('auditowner')
        cls.good = create_realty(owner, trade_type='sale')
        cls.without_trade = create_realty(owner)
        cls.wrong_type = create_realty(owner, trade_type='sale')
        Realty.objects.filter(pk=cls.wrong_type.pk).update(commercial_type='office')

    def run_command(self, *args):
        out = StringIO()
        call_command('audit_realty', *args, stdout=out)
        return out.getvalue()

    def test_report_finds_broken_realty(self):
        """Отчёт показывает объявление без сделки и лишний коммерческий тип"""
        output = self.run_command()
        self.assertIn(f'#{self.without_trade.id}', output)
        self.assertIn(f'#{self.wrong_type.id}', output)
        self.assertNotIn(f'#{self.good.id}', output)

    def test_report_changes_nothing(self):
        """Без --fix данные не трогаются"""
        self.run_command()
        self.without_trade.refresh_from_db()
        self.assertFalse(self.without_trade.is_deleted)

    def test_fix_repairs_broken_realty(self):
        """С --fix лишний тип снимается, объявление без сделки прячется"""
        self.run_command('--fix')

        self.wrong_type.refresh_from_db()
        self.without_trade.refresh_from_db()
        self.good.refresh_from_db()

        self.assertIsNone(self.wrong_type.commercial_type)
        self.assertTrue(self.without_trade.is_deleted)
        self.assertFalse(self.good.is_deleted)


class StreetDirectoryTest(TestCase):
    """Правка адреса не трогает справочник улиц: на улицу ссылаются и соседи."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user('streetowner')
        cls.city = City.objects.create(name='Москва')
        cls.zone = Zone.objects.create(name='Пресненский')
        cls.district = District.objects.create(name='ЦАО')
        cls.street = Street.objects.create(
            name='Тверская', city=cls.city, zone=cls.zone, district=cls.district
        )
        cls.realty = create_realty(cls.owner, trade_type='sale')
        cls.neighbour = create_realty(cls.owner, trade_type='sale')
        for realty in (cls.realty, cls.neighbour):
            realty.address.street = cls.street
            realty.address.save()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def patch_street(self, **street):
        return self.client.patch(
            f'{SALES_URL}{self.realty.sale_profile.id}/',
            {'address': {'street': street}},
            format='json',
        )

    def test_existing_street_is_not_renamed(self):
        """Смена улицы в объявлении не переименовывает улицу у соседей"""
        response = self.patch_street(name='Ленина')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.street.refresh_from_db()
        self.neighbour.refresh_from_db()

        self.assertEqual(self.street.name, 'Тверская')
        self.assertEqual(self.neighbour.address.street.name, 'Тверская')

    def test_zone_and_district_survive_partial_update(self):
        """Район и округ не обнуляются, если их не передали"""
        self.patch_street(name='Ленина')

        self.realty.refresh_from_db()
        street = self.realty.address.street

        self.assertEqual(street.name, 'Ленина')
        self.assertEqual(street.zone_id, self.zone.id)
        self.assertEqual(street.district_id, self.district.id)

    def test_existing_street_is_reused(self):
        """Если такая улица уже есть, новая не заводится"""
        Street.objects.create(
            name='Ленина', city=self.city, zone=self.zone, district=self.district
        )
        before = Street.objects.count()

        self.patch_street(name='Ленина')

        self.assertEqual(Street.objects.count(), before)


class FavoriteBadRequestTest(TestCase):
    """Нечисловой realty_id — 400, а не падение сервера."""

    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('favbadrequest')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_non_numeric_realty_id(self):
        """realty_id: "abc" — 400"""
        response = self.client.post(FAVORITES_URL, {'realty_id': 'abc'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('realty_id', response.json())
