"""Поиск коммерческой недвижимости: назначение с множественным выбором,
новые фильтры, жилой поиск по умолчанию, справочник значений."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty.models import Realty, Rent
from realty_specificities.models import (
    AboutApartment,
    CommercialCharacteristics,
    CommonCharacteristics,
)
from realty_values.models import RealtyAdvStatus, RealtyType
from tests.factories import create_realty, create_user

LIST_URL = '/api/realty/'
COUNT_URL = '/api/realty/count/'
MAP_POINTS_URL = '/api/realty-addresses/map-points/'
OPTIONS_URL = '/api/realty/filter-options/'

WHOLE_MAP = {
    'top_left_latitude': 56.0,
    'top_left_longitude': 37.0,
    'bottom_right_latitude': 55.0,
    'bottom_right_longitude': 38.0,
}


def commercial(owner, type_name, code, trade_type, **characteristics):
    """Коммерческое объявление с характеристиками помещения."""
    realty = create_realty(
        owner,
        realty_type=RealtyType.objects.get(type=type_name),
        trade_type=trade_type,
        commercial_type=code,
        commercial_characteristics=CommercialCharacteristics.objects.create(
            **{'building_type': 'business_center', **characteristics}
        ),
    )
    AboutApartment.objects.filter(pk=realty.about_apartment_id).update(
        number_of_rooms=None
    )
    return realty


class CommercialSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        active, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        owner = create_user('searchowner')

        cls.flat = create_realty(
            owner,
            trade_type='sale',
            common_characteristics=CommonCharacteristics.objects.create(furniture=True),
        )
        cls.office = commercial(
            owner,
            'Офис',
            'office',
            'sale',
            entrance='separate',
            heating='central',
            finishing='office',
            has_furniture=True,
        )
        cls.warehouse = commercial(
            owner,
            'Склад',
            'warehouse',
            'sale',
            building_type='administrative',
            entrance='shared',
            heating='none',
            finishing='none',
            has_furniture=False,
        )
        cls.retail_rent = commercial(
            owner,
            'Торговое помещение',
            'retail',
            'rent',
            building_type='shopping_center',
        )
        cls.free_use_rent = commercial(
            owner, 'Помещение свободного назначения', 'free_use', 'rent'
        )
        Rent.objects.filter(realty=cls.retail_rent).update(
            lease_type='sublease', utilities_included=True
        )
        Rent.objects.filter(realty=cls.free_use_rent).update(
            lease_type='direct', utilities_included=False
        )
        Realty.objects.update(realty_status=active)

    def setUp(self):
        self.client = APIClient()

    def found(self, params):
        response = self.client.get(LIST_URL, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return {item['id'] for item in response.data['results']}

    def commercial_found(self, **params):
        return self.found({'is_commercial': 'true', **params})

    # --- Жилой поиск по умолчанию ---

    def test_default_search_is_residential(self):
        """Поиск без выбора «жилая / коммерческая» показывает только жилую"""
        self.assertEqual(self.found({}), {self.flat.id})

    def test_count_matches_default_search(self):
        """Счётчик по умолчанию тоже считает только жилую"""
        response = self.client.get(COUNT_URL)
        self.assertEqual(response.data['count'], 1)

    def test_residential_and_commercial_explicitly(self):
        """is_commercial=false — жилая, true — коммерческая"""
        self.assertEqual(self.found({'is_commercial': 'false'}), {self.flat.id})
        self.assertEqual(
            self.commercial_found(),
            {
                self.office.id,
                self.warehouse.id,
                self.retail_rent.id,
                self.free_use_rent.id,
            },
        )

    def test_commercial_filters_without_is_commercial(self):
        """Назначение, тип или характеристика без is_commercial не дают пустой выдачи"""
        cases = {
            'commercial_type': ('office', {self.office.id}),
            'realty_type': ('Склад', {self.warehouse.id}),
            'heating': ('central', {self.office.id}),
            'lease_type': ('direct', {self.free_use_rent.id}),
        }
        for name, (value, expected) in cases.items():
            with self.subTest(filter=name):
                self.assertEqual(self.found({name: value}), expected)

    def test_residential_realty_type_without_is_commercial(self):
        """Жилой тип без is_commercial — как раньше"""
        self.assertEqual(self.found({'realty_type': 'Квартира'}), {self.flat.id})

    def test_repeated_purpose_page_title_matches_results(self):
        """При повторе параметра заголовок совпадает с выдачей"""
        response = self.client.get(
            LIST_URL
            + '?is_commercial=true&trade_type=sale'
            + '&commercial_type=warehouse&commercial_type=office'
        )

        self.assertEqual(
            {item['id'] for item in response.data['results']}, {self.office.id}
        )
        self.assertEqual(response.data['page_title'], 'Купить офис в Москве')

    def test_map_points_follow_the_same_rule(self):
        """На карте по умолчанию жилая, с is_commercial=true — коммерческая"""

        def map_ids(query=''):
            response = self.client.post(
                MAP_POINTS_URL + query, WHOLE_MAP, format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return {point['id'] for point in response.data}

        self.assertEqual(map_ids(), {self.flat.id})
        self.assertIn(self.office.id, map_ids('?is_commercial=true'))

    # --- Назначение ---

    def test_several_purposes(self):
        """Назначение с множественным выбором: «Офис + Склад»"""
        self.assertEqual(
            self.commercial_found(commercial_type='office,warehouse'),
            {self.office.id, self.warehouse.id},
        )

    def test_no_purpose_shows_all_commercial_of_trade_type(self):
        """Назначение не выбрано — все коммерческие объявления типа сделки"""
        self.assertEqual(
            self.commercial_found(trade_type='rent'),
            {self.retail_rent.id, self.free_use_rent.id},
        )

    def test_unknown_purpose_is_rejected(self):
        """Неизвестное назначение → 400 со списком допустимых"""
        response = self.client.get(
            LIST_URL, {'is_commercial': 'true', 'commercial_type': 'office,castle'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('castle', response.data['commercial_type'])
        self.assertIn('warehouse', response.data['commercial_type'])

    def test_empty_purpose_means_not_selected(self):
        """Пустое значение и лишняя запятая не ломают поиск"""
        self.assertEqual(
            self.commercial_found(commercial_type='office,'), {self.office.id}
        )
        self.assertEqual(len(self.commercial_found(commercial_type='')), 4)

    def test_page_title_with_several_purposes(self):
        """Несколько назначений — «коммерческое помещение» в заголовке"""
        response = self.client.get(
            LIST_URL,
            {
                'is_commercial': 'true',
                'trade_type': 'sale',
                'commercial_type': 'office,warehouse',
            },
        )

        self.assertEqual(
            response.data['page_title'], 'Купить коммерческое помещение в Москве'
        )
        self.assertEqual(response.data['count'], 2)

    # --- Новые фильтры ---

    def test_room_characteristics_filters(self):
        """Тип здания, вход, отопление, отделка — каждый со множественным выбором"""
        cases = {
            'building_type': ('administrative', {self.warehouse.id}),
            'entrance': ('separate', {self.office.id}),
            'heating': ('central,none', {self.office.id, self.warehouse.id}),
            'finishing': ('office', {self.office.id}),
        }
        for name, (value, expected) in cases.items():
            with self.subTest(filter=name):
                self.assertEqual(self.commercial_found(**{name: value}), expected)

    def test_unknown_characteristic_is_rejected(self):
        """Неизвестное значение фильтра → 400"""
        response = self.client.get(LIST_URL, {'heating': 'fireplace'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('heating', response.data)

    def test_furniture_for_commercial_and_residential(self):
        """Мебель: у коммерческой — из характеристик помещения, у жилой — как раньше"""
        self.assertEqual(self.commercial_found(has_furniture='true'), {self.office.id})
        self.assertEqual(
            self.commercial_found(has_furniture='false', trade_type='sale'),
            {self.warehouse.id},
        )
        self.assertEqual(self.found({'has_furniture': 'true'}), {self.flat.id})

    def test_lease_filters(self):
        """Для аренды: тип аренды и коммунальные платежи"""
        self.assertEqual(
            self.commercial_found(lease_type='sublease'), {self.retail_rent.id}
        )
        self.assertEqual(
            self.commercial_found(utilities_included='false'),
            {self.free_use_rent.id},
        )

    def test_price_and_area_work_for_commercial(self):
        """Цена и площадь работают как раньше"""
        Realty.objects.filter(pk=self.office.pk).update(price=5_000_000)
        AboutApartment.objects.filter(pk=self.warehouse.about_apartment_id).update(
            area=900
        )

        self.assertEqual(self.commercial_found(price_min=2_000_000), {self.office.id})
        self.assertEqual(self.commercial_found(area_min=500), {self.warehouse.id})

    def test_count_respects_new_filters(self):
        """Счётчик учитывает новые фильтры"""
        response = self.client.get(
            COUNT_URL,
            {'is_commercial': 'true', 'commercial_type': 'office,retail'},
        )
        self.assertEqual(response.data['count'], 2)

    # --- Справочник ---

    def test_filter_options_have_commercial_values(self):
        """В справочнике есть все значения для коммерческого поиска"""
        response = self.client.get(OPTIONS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.data['commercial']
        self.assertEqual(
            [item['value'] for item in options['commercial_type']],
            ['office', 'retail', 'warehouse', 'free_use'],
        )
        self.assertIn(
            {'value': 'business_center', 'label': 'Бизнес-центр'},
            options['building_type'],
        )
        for name in ('entrance', 'heating', 'finishing', 'lease_type'):
            with self.subTest(name=name):
                self.assertTrue(options[name])

        office = next(t for t in response.data['realty_type'] if t['type'] == 'Офис')
        self.assertTrue(office['is_commercial'])
