from django.test import TestCase

from realty.serializers.serializers_realty import RealtyCreateSerializer
from realty_values.models import RealtyType
from tests.factories import create_realty, create_user

COMMERCIAL_TYPE_NAMES = [
    'Офис',
    'Торговое помещение',
    'Склад',
    'Помещение свободного назначения',
    'Производственное помещение',
]


class CommercialRealtyTypesSeedTest(TestCase):
    """Справочник коммерческих типов заводится миграцией."""

    def test_commercial_types_exist(self):
        """Тест: все коммерческие типы есть в справочнике"""
        for name in COMMERCIAL_TYPE_NAMES:
            with self.subTest(name=name):
                self.assertTrue(
                    RealtyType.objects.filter(type=name, is_commercial=True).exists()
                )

    def test_residential_types_untouched(self):
        """Тест: миграция не сделала коммерческими жилые типы"""
        residential, _ = RealtyType.objects.get_or_create(
            type='Квартира', defaults={'is_commercial': False}
        )
        self.assertFalse(residential.is_commercial)


class CommercialTypeValidationTest(TestCase):
    """Связка realty_type.is_commercial и commercial_type."""

    def setUp(self):
        self.user = create_user('commercialowner')
        self.residential, _ = RealtyType.objects.get_or_create(
            type='Квартира', defaults={'is_commercial': False}
        )
        self.office = RealtyType.objects.get(type='Офис')
        self.realty = create_realty(self.user, realty_type=self.residential)

    def test_commercial_type_on_residential_is_rejected(self):
        """Тест: тип коммерции у жилого объекта → ошибка"""
        serializer = RealtyCreateSerializer(
            instance=self.realty, data={'commercial_type': 'office'}, partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('commercial_type', serializer.errors)

    def test_commercial_realty_without_type_is_rejected(self):
        """Тест: коммерческий объект без типа коммерции → ошибка"""
        serializer = RealtyCreateSerializer(
            instance=self.realty,
            data={'realty_type': self.office.id},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('commercial_type', serializer.errors)

    def test_commercial_realty_with_type_is_accepted(self):
        """Тест: коммерческий объект с типом коммерции → проходит"""
        serializer = RealtyCreateSerializer(
            instance=self.realty,
            data={'realty_type': self.office.id, 'commercial_type': 'office'},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_residential_without_commercial_type_is_accepted(self):
        """Тест: жилой объект без типа коммерции → проходит"""
        serializer = RealtyCreateSerializer(
            instance=self.realty, data={'price': 2000000}, partial=True
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_clearing_commercial_type_on_commercial_realty_is_rejected(self):
        """Тест: у коммерческого объекта нельзя стереть тип коммерции"""
        self.realty.realty_type = self.office
        self.realty.commercial_type = 'office'
        self.realty.save(update_fields=['realty_type', 'commercial_type'])

        serializer = RealtyCreateSerializer(
            instance=self.realty, data={'commercial_type': None}, partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('commercial_type', serializer.errors)
