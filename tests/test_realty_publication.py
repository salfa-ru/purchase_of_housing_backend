"""Дата публикации проставляется при выходе объявления в эфир, а список
не повторяет одно и то же объявление на соседних страницах."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config import constants
from realty.models import Realty
from realty_values.models import RealtyAdvStatus
from tests.factories import create_realty, create_user

LIST_URL = '/api/realty/'


class PublishedAtTest(TestCase):
    """Сигналы приложения realty подключены: без них дата публикации
    оставалась пустой, ломая сортировку «сначала новые»."""

    @classmethod
    def setUpTestData(cls):
        # Статусы заводятся с теми же id, что и на боевой базе: сигналы
        # сверяют их по id из констант, а не по названию.
        RealtyAdvStatus.objects.all().delete()
        cls.active = RealtyAdvStatus.objects.create(
            id=constants.STATUS_ACTIVE_ID, status=constants.ADVERTISMENT_STATUS
        )
        cls.moderation = RealtyAdvStatus.objects.create(
            id=constants.STATUS_ON_MODERATION_ID, status='На модерации'
        )
        cls.archived = RealtyAdvStatus.objects.create(
            id=constants.STATUS_ARCHIVED_ID, status='В архиве'
        )
        cls.owner = create_user('publishowner')

    def test_published_at_is_set_on_publication(self):
        """При переходе в «Активно» появляется дата публикации"""
        realty = create_realty(
            self.owner, trade_type='sale', realty_status=self.moderation
        )
        self.assertIsNone(realty.published_at)

        realty.realty_status = self.active
        realty.save()
        realty.refresh_from_db()

        self.assertIsNotNone(realty.published_at)

    def test_published_at_is_cleared_when_taken_down(self):
        """Уход из «Активно» дату публикации снимает"""
        realty = create_realty(
            self.owner, trade_type='sale', realty_status=self.moderation
        )
        realty.realty_status = self.active
        realty.save()

        realty.realty_status = self.archived
        realty.save()
        realty.refresh_from_db()

        self.assertIsNone(realty.published_at)


class ListPaginationTest(TestCase):
    """Одно объявление не попадает на две страницы подряд."""

    PAGE_SIZE = 10
    TOTAL = 25

    @classmethod
    def setUpTestData(cls):
        owner = create_user('paginationowner')
        active, _ = RealtyAdvStatus.objects.get_or_create(
            status=constants.ADVERTISMENT_STATUS
        )
        for _ in range(cls.TOTAL):
            realty = create_realty(owner, trade_type='sale')
            Realty.objects.filter(pk=realty.pk).update(realty_status=active)

    def page(self, number):
        response = APIClient().get(LIST_URL, {'page': number})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return [item['id'] for item in response.data['results']]

    def test_pages_do_not_repeat_realty(self):
        """У объявлений без даты публикации страницы всё равно не пересекаются"""
        collected = []
        for number in range(1, self.TOTAL // self.PAGE_SIZE + 2):
            collected.extend(self.page(number))

        self.assertEqual(len(collected), self.TOTAL)
        self.assertEqual(len(set(collected)), self.TOTAL)

    def test_order_is_stable_between_requests(self):
        """Повторный запрос той же страницы даёт тот же порядок"""
        self.assertEqual(self.page(1), self.page(1))
