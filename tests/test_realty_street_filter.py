"""Фильтр GET /api/realty/?address_street=..."""

from django.test import TestCase
from django.urls import reverse

from config import constants
from realty_addresses.models import City, Metro, MetroLine, Street
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user


class AddressStreetFilterTest(TestCase):
    """Поиск по улице: полная фраза, сокращения, регистр, перечисление."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('realty:realty-list')
        cls.user = create_user('streetowner')
        cls.city = City.objects.create(name='Москва')
        line, _ = MetroLine.objects.get_or_create(
            id=1,
            defaults={
                'line_id': '1',
                'name': 'Тестовая',
                'name_full': 'Тестовая линия',
                'color': 'FF0000',
            },
        )
        cls.metro = Metro.objects.create(id=1, name='Алтуфьево', line=line)

        cls.active_status, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        cls.realty_by_street = {
            name: cls._create_on_street(name)
            for name in (
                'ул Габричевского',
                'пр-кт Защитников Москвы',
                'Алтуфьевское шоссе',
                'ул. Ленина',
                'Тульская',
            )
        }

    @classmethod
    def _create_on_street(cls, street_name):
        realty = create_realty(cls.user)
        realty.realty_status = cls.active_status
        realty.save()
        realty.address.street = Street.objects.create(name=street_name, city=cls.city)
        realty.address.save()
        return realty

    def found_streets(self, value):
        """Названия улиц найденных объявлений."""
        response = self.client.get(self.url, {'address_street': value})
        self.assertEqual(response.status_code, 200)
        return {item['street'] for item in response.json()['results']}

    def test_full_phrase(self):
        """Тест: поиск по полной фразе «ул Габричевского»"""
        self.assertEqual(self.found_streets('ул Габричевского'), {'ул Габричевского'})

    def test_compound_street_name(self):
        """Тест: составное название с сокращением через тире"""
        self.assertEqual(
            self.found_streets('пр-кт Защитников Москвы'),
            {'пр-кт Защитников Москвы'},
        )

    def test_single_word(self):
        """Тест: однословный запрос по части названия"""
        self.assertEqual(self.found_streets('Алтуфьевское'), {'Алтуфьевское шоссе'})

    def test_street_type_abbreviation(self):
        """Тест: «ул» находит и «ул », и «ул.», и не цепляет «Тульская»"""
        self.assertEqual(self.found_streets('ул'), {'ул Габричевского', 'ул. Ленина'})

    def test_abbreviation_with_dot(self):
        """Тест: «ул.» равнозначно «ул»"""
        self.assertEqual(self.found_streets('ул.'), {'ул Габричевского', 'ул. Ленина'})

    def test_abbreviation_matches_full_form(self):
        """Тест: «шоссе» и «ш.» — одно и то же"""
        self.assertEqual(self.found_streets('ш.'), {'Алтуфьевское шоссе'})

    def test_case_insensitive(self):
        """Тест: регистр не важен"""
        self.assertEqual(self.found_streets('УЛ ГАБРИЧЕВСКОГО'), {'ул Габричевского'})

    def test_word_order_does_not_matter(self):
        """Тест: порядок слов не важен"""
        self.assertEqual(
            self.found_streets('Москвы Защитников'), {'пр-кт Защитников Москвы'}
        )

    def test_several_streets_by_comma(self):
        """Тест: несколько улиц через запятую"""
        self.assertEqual(
            self.found_streets('ул Габричевского, Алтуфьевское'),
            {'ул Габричевского', 'Алтуфьевское шоссе'},
        )

    def test_comma_without_space(self):
        """Тест: запятая без пробела"""
        self.assertEqual(
            self.found_streets('Тульская,Алтуфьевское'),
            {'Тульская', 'Алтуфьевское шоссе'},
        )

    def test_unknown_street_returns_nothing(self):
        """Тест: несуществующая улица — пустой результат"""
        self.assertEqual(self.found_streets('Несуществующая'), set())

    def test_blank_value_does_not_filter(self):
        """Тест: пустое значение не фильтрует"""
        self.assertEqual(len(self.found_streets('   ')), len(self.realty_by_street))

    def test_search_by_metro(self):
        """Тест: тот же параметр ищет и по станции метро"""
        realty = self.realty_by_street['Тульская']
        realty.address.metro = self.metro
        realty.address.save()
        self.assertEqual(self.found_streets('Алтуфьево'), {'Тульская'})
