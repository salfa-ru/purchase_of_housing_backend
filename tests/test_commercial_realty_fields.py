"""Поля коммерческого объявления: характеристики помещения, условия аренды,
необязательные комнаты и этаж, который не нужен в подвале."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty.models import Realty, Rent, Sale
from realty.serializers.serializers_realty import (
    COMMERCIAL_REQUIRED,
    FLOOR_REQUIRED,
    ROOMS_REQUIRED,
)
from realty.serializers.serializers_rent import LEASE_TYPE_REQUIRED
from realty_addresses.models import City
from realty_specificities.models import CommercialCharacteristics
from realty_values.models import (
    CommunicationMethod,
    RealtyType,
    RoomsNumber,
    TradeParticipant,
)
from tests.factories import create_realty, create_user

SALES_URL = '/api/realty/sales/'
RENTS_URL = '/api/realty/rents/'

FULL_CHARACTERISTICS = {
    'building_type': 'business_center',
    'entrance': 'separate',
    'ceiling_height': 3.2,
    'heating': 'central',
    'finishing': 'office',
    'has_furniture': True,
    'is_basement': False,
    'is_socle': True,
    'is_attic': False,
}


def detail_url(realty_id):
    return f'/api/realty/{realty_id}/'


class CommercialRealtyFieldsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user('commercialseller')
        cls.office = RealtyType.objects.get(type='Офис')
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

    def realty_payload(self, commercial=True, **overrides):
        payload = {
            'realty_type': self.office.id if commercial else self.flat.id,
            'address': {
                'house_number': '1',
                'latitude': 55.75,
                'longitude': 37.6,
                'street': {'name': 'Тверская', 'city': self.city.id},
            },
            'about_apartment': {'area': 60, 'floor': 1, 'floors_number': 5},
            'description': 'Помещение',
            'price': 100000,
            'owner_type': self.owner_type.id,
            'communication_method': self.method.id,
        }
        if commercial:
            payload['commercial_type'] = 'office'
            payload['commercial_characteristics'] = dict(FULL_CHARACTERISTICS)
        else:
            payload['about_apartment']['number_of_rooms'] = self.rooms.id
        payload.update(overrides)
        return payload

    def create_sale(self, **kwargs):
        return self.client.post(SALES_URL, self.realty_payload(**kwargs), format='json')

    def create_rent(self, commercial=True, **rent_fields):
        payload = {'realty': self.realty_payload(commercial=commercial), **rent_fields}
        return self.client.post(RENTS_URL, payload, format='json')

    def detail(self, realty_id):
        return self.client.get(detail_url(realty_id)).data

    # --- Создание продажи ---

    def test_commercial_sale_saves_all_characteristics(self):
        """Коммерческая продажа сохраняет все характеристики помещения"""
        response = self.create_sale()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        data = self.detail(response.data['id'])
        self.assertEqual(data['commercial_characteristics'], FULL_CHARACTERISTICS)

    def test_commercial_sale_without_rooms_is_accepted(self):
        """У коммерческого помещения количество комнат не нужно"""
        response = self.create_sale()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        realty = Realty.objects.get(pk=response.data['id'])
        self.assertIsNone(realty.about_apartment.number_of_rooms)
        self.assertIn('Офис', str(realty))

    def test_only_building_type_is_required(self):
        """Из характеристик обязателен только тип здания"""
        response = self.create_sale(
            commercial_characteristics={'building_type': 'administrative'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_commercial_without_characteristics_is_rejected(self):
        """Коммерческое объявление без характеристик → 400"""
        payload = self.realty_payload()
        del payload['commercial_characteristics']

        response = self.client.post(SALES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data['commercial_characteristics'][0]), COMMERCIAL_REQUIRED
        )

    def test_characteristics_without_building_type_are_rejected(self):
        """Характеристики без типа здания → 400"""
        response = self.create_sale(commercial_characteristics={'heating': 'central'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('commercial_characteristics', response.data)

    def test_unknown_choice_is_rejected(self):
        """Значение не из списка → 400"""
        response = self.create_sale(
            commercial_characteristics={'building_type': 'castle'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('building_type', response.data['commercial_characteristics'])

    def test_ceiling_height_out_of_range_is_rejected(self):
        """Высота потолков вне допустимого диапазона → 400"""
        response = self.create_sale(
            commercial_characteristics={
                'building_type': 'administrative',
                'ceiling_height': constants.MIN_CEILING_HEIGHT - 0.1,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ceiling_height', response.data['commercial_characteristics'])

    def test_residential_with_characteristics_is_rejected(self):
        """У жилой недвижимости коммерческих характеристик нет → 400"""
        response = self.create_sale(
            commercial=False,
            commercial_characteristics={'building_type': 'administrative'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('commercial_characteristics', response.data)

    def test_residential_without_rooms_is_rejected(self):
        """У жилой недвижимости количество комнат по-прежнему обязательно"""
        payload = self.realty_payload(commercial=False)
        del payload['about_apartment']['number_of_rooms']

        response = self.client.post(SALES_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data['about_apartment']['number_of_rooms']), ROOMS_REQUIRED
        )

    def test_residential_sale_still_works(self):
        """Жилая продажа создаётся как раньше"""
        response = self.create_sale(commercial=False)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNone(
            self.detail(response.data['id'])['commercial_characteristics']
        )

    # --- Описание ---

    def test_description_limit_is_the_same_for_commercial(self):
        """Лимит описания у коммерческой недвижимости такой же, как у жилой"""
        long_text = 'а' * constants.DESCRIPTION_LENGTH
        self.assertEqual(self.create_sale(description=long_text).status_code, 201)

        response = self.create_sale(description=long_text + 'а')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)

    # --- Этаж ---

    def without_floor(self, **overrides):
        """Объявление без номера этажа."""
        payload = self.realty_payload(**overrides)
        del payload['about_apartment']['floor']
        return self.client.post(SALES_URL, payload, format='json')

    def test_basement_realty_is_created_without_floor(self):
        """У помещения в подвале номер этажа можно не указывать"""
        characteristics = {'building_type': 'administrative', 'is_basement': True}
        response = self.without_floor(commercial_characteristics=characteristics)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        realty = Realty.objects.get(pk=response.data['id'])
        self.assertIsNone(realty.about_apartment.floor)
        self.assertIsNone(self.detail(realty.id)['about_apartment']['floor'])

    def test_socle_and_attic_also_allow_empty_floor(self):
        """Цоколь и мансарда тоже разрешают не указывать этаж"""
        for mark in ('is_socle', 'is_attic'):
            with self.subTest(mark=mark):
                response = self.without_floor(
                    commercial_characteristics={
                        'building_type': 'administrative',
                        mark: True,
                    }
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_commercial_without_marks_needs_floor(self):
        """Без отметки этажа номер этажа обязателен и у коммерческого помещения"""
        response = self.without_floor(
            commercial_characteristics={'building_type': 'administrative'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['about_apartment']['floor']), FLOOR_REQUIRED)

    def test_residential_needs_floor(self):
        """У жилой недвижимости этаж обязателен"""
        response = self.without_floor(commercial=False)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['about_apartment']['floor']), FLOOR_REQUIRED)

    def test_floor_mark_cannot_be_removed_while_floor_is_empty(self):
        """Снять отметку подвала, не указав этаж, нельзя"""
        characteristics = {'building_type': 'administrative', 'is_basement': True}
        realty_id = self.without_floor(commercial_characteristics=characteristics).data[
            'id'
        ]
        sale = Sale.objects.get(realty_id=realty_id)

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/',
            {'commercial_characteristics': {'is_basement': False}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['about_apartment']['floor']), FLOOR_REQUIRED)

    def test_floor_can_be_filled_in_later(self):
        """Этаж можно дозаполнить при изменении"""
        characteristics = {'building_type': 'administrative', 'is_basement': True}
        realty_id = self.without_floor(commercial_characteristics=characteristics).data[
            'id'
        ]
        sale = Sale.objects.get(realty_id=realty_id)

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/',
            {
                'about_apartment': {'floor': 2},
                'commercial_characteristics': {'is_basement': False},
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(self.detail(realty_id)['about_apartment']['floor'], 2)

    # --- Аренда ---

    def test_commercial_rent_saves_lease_terms(self):
        """Коммерческая аренда сохраняет тип аренды и коммуналку"""
        response = self.create_rent(lease_type='sublease', utilities_included=True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        rent = Rent.objects.get(pk=response.data['id'])
        self.assertEqual(rent.lease_type, 'sublease')
        self.assertTrue(rent.utilities_included)

        detail = self.detail(rent.realty_id)
        self.assertEqual(detail['rent']['lease_type'], 'sublease')
        self.assertTrue(detail['rent']['utilities_included'])
        self.assertEqual(
            detail['commercial_characteristics']['building_type'], 'business_center'
        )

    def test_commercial_rent_without_lease_type_is_rejected(self):
        """Коммерческая аренда без типа аренды → 400"""
        response = self.create_rent()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['lease_type'][0]), LEASE_TYPE_REQUIRED)

    def test_residential_rent_with_lease_terms_is_rejected(self):
        """У жилой аренды типа аренды и коммуналки нет → 400"""
        response = self.create_rent(
            commercial=False, lease_type='direct', utilities_included=False
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('lease_type', response.data)
        self.assertIn('utilities_included', response.data)

    def test_residential_rent_still_works(self):
        """Жилая аренда создаётся как раньше"""
        response = self.create_rent(commercial=False)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    # --- Изменение ---

    def old_commercial_sale(self):
        """Коммерческое объявление, созданное до появления новых полей."""
        realty = create_realty(
            self.user,
            realty_type=self.office,
            trade_type='sale',
            commercial_type='office',
        )
        return Sale.objects.get(realty=realty)

    def test_old_commercial_realty_can_be_edited_without_new_fields(self):
        """Старое коммерческое объявление редактируется без новых полей"""
        sale = self.old_commercial_sale()

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/', {'price': 555}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        sale.realty.refresh_from_db()
        self.assertEqual(sale.realty.price, 555)

    def test_old_commercial_realty_gets_characteristics_on_edit(self):
        """Старому объявлению характеристики добавляются при изменении"""
        sale = self.old_commercial_sale()

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/',
            {'commercial_characteristics': {'building_type': 'shopping_center'}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        sale.realty.refresh_from_db()
        self.assertEqual(
            sale.realty.commercial_characteristics.building_type, 'shopping_center'
        )

    def test_partial_characteristics_without_building_type_on_old_realty(self):
        """Старому объявлению нельзя добавить характеристики без типа здания"""
        sale = self.old_commercial_sale()

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/',
            {'commercial_characteristics': {'heating': 'central'}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CommercialCharacteristics.objects.exists())

    def test_characteristics_are_updated_partially(self):
        """Изменение одной характеристики не стирает остальные"""
        realty_id = self.create_sale().data['id']
        sale = Sale.objects.get(realty_id=realty_id)

        response = self.client.patch(
            f'{SALES_URL}{sale.id}/',
            {'commercial_characteristics': {'heating': 'autonomous'}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        characteristics = self.detail(realty_id)['commercial_characteristics']
        self.assertEqual(characteristics['heating'], 'autonomous')
        self.assertEqual(characteristics['building_type'], 'business_center')

    def test_lease_type_is_updated(self):
        """Тип аренды меняется через изменение аренды"""
        rent_id = self.create_rent(lease_type='direct').data['id']

        response = self.client.patch(
            f'{RENTS_URL}{rent_id}/', {'lease_type': 'sublease'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(Rent.objects.get(pk=rent_id).lease_type, 'sublease')

    def test_lease_type_cannot_be_cleared_on_commercial_rent(self):
        """У коммерческой аренды нельзя стереть тип аренды"""
        rent_id = self.create_rent(lease_type='direct').data['id']

        response = self.client.patch(
            f'{RENTS_URL}{rent_id}/', {'lease_type': None}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
