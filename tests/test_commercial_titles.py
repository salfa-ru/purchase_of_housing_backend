"""Карточка и выдача коммерческой недвижимости: название объекта, заголовок
страницы, новые поля в списке и смешанная выдача на главной."""

from django.test import SimpleTestCase, TestCase
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty import titles
from realty.models import Realty, Rent
from realty_specificities.models import AboutApartment, CommercialCharacteristics
from realty_values.models import RealtyAdvStatus, RealtyType
from tests.factories import create_realty, create_user

LIST_URL = '/api/realty/'
LATEST_URL = '/api/realty/latest/'
COMMERCIAL = {'is_commercial': 'true'}


class PageTitleVariantsTest(SimpleTestCase):
    def test_all_ten_variants(self):
        """Все 10 заголовков из ТЗ собираются в одном месте"""
        expected = {
            ('rent', ('office',)): 'Снять офис в Москве',
            ('rent', ('retail',)): 'Снять торговое помещение в Москве',
            ('rent', ('warehouse',)): 'Снять склад в Москве',
            ('rent', ('free_use',)): 'Снять помещение свободного назначения в Москве',
            ('rent', ('office', 'warehouse')): 'Снять коммерческое помещение в Москве',
            ('sale', ('office',)): 'Купить офис в Москве',
            ('sale', ('retail',)): 'Купить торговое помещение в Москве',
            ('sale', ('warehouse',)): 'Купить склад в Москве',
            ('sale', ('free_use',)): 'Купить помещение свободного назначения в Москве',
            ('sale', ('retail', 'free_use')): 'Купить коммерческое помещение в Москве',
        }
        for (trade_type, types), title in expected.items():
            with self.subTest(trade_type=trade_type, types=types):
                self.assertEqual(titles.page_title(trade_type, types), title)

    def test_no_type_selected(self):
        """Тип не выбран — «коммерческое помещение»"""
        self.assertEqual(
            titles.page_title('sale', []), 'Купить коммерческое помещение в Москве'
        )

    def test_same_type_twice_is_one_type(self):
        """Повтор одного типа — это один тип"""
        self.assertEqual(
            titles.page_title('rent', ['office', 'office']), 'Снять офис в Москве'
        )

    def test_unknown_trade_type(self):
        """Без типа сделки заголовка нет"""
        self.assertIsNone(titles.page_title('', ['office']))


class CommercialCardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        active, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        owner = create_user('cardowner')

        cls.flat = create_realty(owner, trade_type='sale')
        cls.retail = create_realty(
            owner,
            realty_type=RealtyType.objects.get(type='Торговое помещение'),
            trade_type='rent',
            commercial_type='retail',
        )
        cls.office = create_realty(
            owner,
            realty_type=RealtyType.objects.get(type='Офис'),
            trade_type='sale',
            commercial_type='office',
        )
        Realty.objects.update(realty_status=active)

        # Коммерческое помещение в подвале: ни комнат, ни номера этажа
        AboutApartment.objects.filter(pk=cls.retail.about_apartment_id).update(
            number_of_rooms=None, floor=None, area=140, floors_number=5
        )
        AboutApartment.objects.filter(pk=cls.office.about_apartment_id).update(
            number_of_rooms=None, area=60.5
        )
        characteristics = CommercialCharacteristics.objects.create(
            building_type='shopping_center', is_basement=True
        )
        Realty.objects.filter(pk=cls.retail.pk).update(
            commercial_characteristics=characteristics
        )
        Rent.objects.filter(realty=cls.retail).update(
            lease_type='sublease', utilities_included=True
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=create_user('viewer'))

    def listed(self, params=None, client=None):
        response = (client or self.client).get(LIST_URL, params or {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def item(self, response, realty):
        return next(i for i in response.data['results'] if i['id'] == realty.id)

    # --- Список ---

    def test_list_with_commercial_realty_works(self):
        """Список с коммерческим объявлением без комнат не падает"""
        item = self.item(self.listed(COMMERCIAL), self.retail)
        self.assertIsNone(item['number_of_rooms'])
        self.assertEqual(item['floors_number'], '—/5 этаж')
        self.assertEqual(self.item(self.listed(), self.flat)['number_of_rooms'], '2')

    def test_list_for_anonymous_with_commercial_realty_works(self):
        """Анонимный список тоже не падает и отдаёт название"""
        response = self.listed(COMMERCIAL, client=APIClient())

        self.assertEqual(
            self.item(response, self.retail)['title'], 'Торговое помещение, 140 м²'
        )

    def test_list_gives_commercial_fields(self):
        """В списке есть характеристики помещения и условия аренды"""
        item = self.item(self.listed(COMMERCIAL), self.retail)

        self.assertEqual(item['title'], 'Торговое помещение, 140 м²')
        self.assertEqual(
            item['commercial_characteristics']['building_type'], 'shopping_center'
        )
        self.assertTrue(item['commercial_characteristics']['is_basement'])
        self.assertEqual(item['rent']['lease_type'], 'sublease')
        self.assertTrue(item['rent']['utilities_included'])

    def test_residential_has_no_title(self):
        """У жилой недвижимости названия и характеристик помещения нет"""
        item = self.item(self.listed(), self.flat)

        self.assertIsNone(item['title'])
        self.assertIsNone(item['commercial_characteristics'])

    # --- Заголовок страницы поиска ---

    def test_search_page_title_for_one_type(self):
        """Поиск по одному типу — тип в заголовке"""
        response = self.listed(
            {'is_commercial': 'true', 'trade_type': 'rent', 'commercial_type': 'retail'}
        )

        self.assertEqual(
            response.data['page_title'], 'Снять торговое помещение в Москве'
        )
        self.assertEqual([i['id'] for i in response.data['results']], [self.retail.id])

    def test_search_page_title_without_type(self):
        """Тип не выбран — «коммерческое помещение»"""
        response = self.listed({'is_commercial': 'true', 'trade_type': 'sale'})

        self.assertEqual(
            response.data['page_title'], 'Купить коммерческое помещение в Москве'
        )
        self.assertEqual([i['id'] for i in response.data['results']], [self.office.id])

    def test_search_page_title_with_russian_trade_type(self):
        """Тип сделки можно передать и по-русски"""
        response = self.listed({'is_commercial': 'true', 'trade_type': 'Аренда'})

        self.assertEqual(
            response.data['page_title'], 'Снять коммерческое помещение в Москве'
        )

    def test_residential_search_has_no_page_title(self):
        """В поиске жилой недвижимости заголовка нет"""
        response = self.listed({'trade_type': 'sale'})
        self.assertIsNone(response.data['page_title'])

    # --- Детальная карточка ---

    def test_detail_gives_title_and_page_title(self):
        """Детальная карточка: название и заголовок страницы"""
        response = self.client.get(f'/api/realty/{self.office.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Офис, 60.5 м²')
        self.assertEqual(response.data['page_title'], 'Купить офис в Москве')

    def test_detail_rent_page_title(self):
        """У аренды заголовок начинается со «Снять»"""
        response = self.client.get(f'/api/realty/{self.retail.id}/')

        self.assertEqual(
            response.data['page_title'], 'Снять торговое помещение в Москве'
        )

    def test_detail_residential_has_no_titles(self):
        """У жилой недвижимости в детальной карточке заголовков нет"""
        response = self.client.get(f'/api/realty/{self.flat.id}/')

        self.assertIsNone(response.data['title'])
        self.assertIsNone(response.data['page_title'])

    # --- Главная ---

    def test_home_mixes_residential_and_commercial(self):
        """На главной в блоке «Для покупки» жилые и коммерческие вместе"""
        response = APIClient().get(LATEST_URL, {'trade_type': 'sale'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {self.flat.id, self.office.id})


class SearchSchemaTest(SimpleTestCase):
    def test_search_keeps_description_and_page_title_in_swagger(self):
        """В Swagger у поиска есть описание и page_title в ответе"""
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema['paths']['/api/realty/']['get']

        self.assertIn('lat_min', operation['description'])
        response = operation['responses']['200']['content']['application/json']
        ref = response['schema']['$ref'].split('/')[-1]
        properties = schema['components']['schemas'][ref]['properties']
        self.assertIn('page_title', properties)
