"""Выделенная область на карте: фильтр lat_min/lat_max/lon_min/lon_max работает
в списке, счётчике и точках на карте вместе с остальными фильтрами."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty.filters import AREA_INCOMPLETE, AREA_LAT_ORDER
from realty.models import Realty
from realty_addresses.models import Address
from realty_addresses.serializers import MAP_LATITUDE_ORDER
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user

LIST_URL = '/api/realty/'
COUNT_URL = '/api/realty/count/'
MAP_POINTS_URL = '/api/realty-addresses/map-points/'
MAP_POINT_REALTY_URL = '/api/realty-addresses/map-point-realty/'

AREA = {'lat_min': 55.70, 'lat_max': 55.80, 'lon_min': 37.50, 'lon_max': 37.70}

WHOLE_MAP = {
    'top_left_latitude': 56.0,
    'top_left_longitude': 37.0,
    'bottom_right_latitude': 55.0,
    'bottom_right_longitude': 38.0,
}


def place(realty, latitude, longitude):
    Address.objects.filter(pk=realty.address_id).update(
        latitude=latitude, longitude=longitude
    )


class MapAreaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        active, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        owner = create_user('mapowner')

        cls.inside = create_realty(owner)
        cls.inside_expensive = create_realty(owner)
        cls.on_border = create_realty(owner)
        cls.outside = create_realty(owner)
        Realty.objects.update(realty_status=active, price=1_000_000)
        Realty.objects.filter(pk=cls.inside_expensive.pk).update(price=9_000_000)

        place(cls.inside, 55.75, 37.60)
        place(cls.inside_expensive, 55.76, 37.61)
        place(cls.on_border, AREA['lat_max'], AREA['lon_min'])
        place(cls.outside, 55.60, 37.40)

    def setUp(self):
        self.client = APIClient()

    def listed_ids(self, params):
        response = self.client.get(LIST_URL, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return {item['id'] for item in response.data['results']}

    def map_ids(self, params=None):
        url = MAP_POINTS_URL
        if params:
            url += '?' + '&'.join(f'{key}={value}' for key, value in params.items())
        response = self.client.post(url, WHOLE_MAP, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return {point['id'] for point in response.data}

    def test_list_without_area_returns_everything(self):
        """Без области список не ограничивается"""
        self.assertEqual(len(self.listed_ids({})), 4)

    def test_list_keeps_only_realty_inside_area(self):
        """В списке остаются только объявления внутри области, граница включается"""
        self.assertEqual(
            self.listed_ids(AREA),
            {self.inside.id, self.inside_expensive.id, self.on_border.id},
        )

    def test_area_works_together_with_other_filters(self):
        """Область сочетается с остальными фильтрами"""
        self.assertEqual(
            self.listed_ids({**AREA, 'price_max': 2_000_000}),
            {self.inside.id, self.on_border.id},
        )

    def test_count_respects_area(self):
        """Счётчик найденных учитывает область"""
        response = self.client.get(COUNT_URL, AREA)
        self.assertEqual(response.data['count'], 3)

    def test_incomplete_area_is_rejected(self):
        """Часть границ → 400 с объяснением"""
        response = self.client.get(LIST_URL, {'lat_min': 55.7, 'lat_max': 55.8})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], AREA_INCOMPLETE)

    def test_reversed_area_is_rejected(self):
        """Минимум больше максимума → 400"""
        response = self.client.get(LIST_URL, {**AREA, 'lat_min': 55.9, 'lat_max': 55.7})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['lat_min'], AREA_LAT_ORDER)

    def test_latitude_out_of_range_is_rejected(self):
        """Широта за пределами ±90 → 400"""
        response = self.client.get(LIST_URL, {**AREA, 'lat_max': 91})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('lat_max', response.data)

    def test_tiny_area_is_accepted(self):
        """Очень маленькая область — допустима"""
        self.assertEqual(
            self.listed_ids(
                {'lat_min': 55.75, 'lat_max': 55.75, 'lon_min': 37.6, 'lon_max': 37.6}
            ),
            {self.inside.id},
        )

    def test_map_points_inside_visible_part(self):
        """Точки на карте отдаются по видимой части карты"""
        self.assertEqual(len(self.map_ids()), 4)

    def test_map_points_respect_selected_area(self):
        """Выделенная область ограничивает точки на карте"""
        self.assertEqual(
            self.map_ids(AREA),
            {self.inside.id, self.inside_expensive.id, self.on_border.id},
        )

    def test_map_points_respect_other_filters(self):
        """Точки на карте перефильтровываются вместе с областью"""
        self.assertEqual(
            self.map_ids({**AREA, 'price_min': 5_000_000}),
            {self.inside_expensive.id},
        )

    def test_map_points_with_swapped_corners_are_rejected(self):
        """Перепутанные углы карты → 400 с объяснением"""
        corners = {
            **WHOLE_MAP,
            'top_left_latitude': 55.0,
            'bottom_right_latitude': 56.0,
        }
        response = self.client.post(MAP_POINTS_URL, corners, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['top_left_latitude'][0]), MAP_LATITUDE_ORDER)

    def test_map_points_skip_deleted_realty(self):
        """Удалённое объявление на карту не попадает"""
        Realty.objects.filter(pk=self.inside.pk).update(is_deleted=True)
        self.assertNotIn(self.inside.id, self.map_ids())

    def test_map_point_realty_returns_realty_in_point(self):
        """Объявления в точке на карте отдаются без ошибок"""
        user = create_user('mapviewer')
        self.client.force_authenticate(user=user)

        response = self.client.post(
            MAP_POINT_REALTY_URL,
            {'latitude': 55.75, 'longitude': 37.60},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [self.inside.id])


class MapWithoutActiveStatusTest(TestCase):
    def test_map_points_without_active_status_do_not_crash(self):
        """Нет статуса «Активно» в базе → пустой ответ, а не 500"""
        response = APIClient().post(MAP_POINTS_URL, WHOLE_MAP, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
