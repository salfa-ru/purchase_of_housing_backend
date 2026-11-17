"""Поиск одинаково строг ко всем параметрам, а справочник фильтров отдаёт
значения для всех фильтров, которые есть в поиске."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

LIST_URL = '/api/realty/'
OPTIONS_URL = '/api/realty/filter-options/'


class BooleanFilterValidationTest(TestCase):
    """Опечатка в булевом параметре — 400, а не молча пустой фильтр."""

    def setUp(self):
        self.client = APIClient()

    def test_unknown_is_commercial_value_is_rejected(self):
        """is_commercial=maybe — 400, как и неизвестная отделка"""
        response = self.client.get(LIST_URL, {'is_commercial': 'maybe'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_commercial', response.json())

    def test_unknown_has_furniture_value_is_rejected(self):
        """То же для мебели"""
        response = self.client.get(LIST_URL, {'has_furniture': 'yes'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('has_furniture', response.json())

    def test_unknown_finishing_value_is_still_rejected(self):
        """Проверка списков кодов осталась прежней"""
        response = self.client.get(
            LIST_URL, {'is_commercial': 'true', 'finishing': 'foo'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('finishing', response.json())

    def test_allowed_boolean_spellings_pass(self):
        """true, false, 1 и 0 принимаются"""
        for value in ('true', 'false', '1', '0', 'True', 'FALSE'):
            with self.subTest(value=value):
                response = self.client.get(LIST_URL, {'is_commercial': value})
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_value_is_treated_as_absent(self):
        """Пустое значение фильтра не ломает запрос"""
        response = self.client.get(LIST_URL, {'is_commercial': ''})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FilterOptionsTest(TestCase):
    """В справочнике есть всё, что принимает поиск коммерческой недвижимости."""

    def options(self):
        response = APIClient().get(OPTIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()['commercial']

    def test_commercial_section_has_every_filter(self):
        """Фронту не нужно хранить значения у себя"""
        expected = {
            'commercial_type',
            'building_type',
            'entrance',
            'heating',
            'finishing',
            'lease_type',
            'has_furniture',
            'utilities_included',
        }
        self.assertEqual(set(self.options()), expected)

    def test_boolean_filters_have_labels(self):
        """У мебели и коммунальных платежей есть подписи для экрана"""
        commercial = self.options()

        self.assertEqual(
            commercial['has_furniture'],
            [
                {'value': True, 'label': 'С мебелью'},
                {'value': False, 'label': 'Без мебели'},
            ],
        )
        self.assertEqual(
            commercial['utilities_included'],
            [
                {'value': True, 'label': 'Включены'},
                {'value': False, 'label': 'Не включены'},
            ],
        )
