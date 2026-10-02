"""Справочник вопросов: пагинация и число запросов в базу."""

from django.test import TestCase
from rest_framework.test import APIClient

from questions.models import Question, QuestionSection, QuestionType

ALL_QUESTIONS_URL = '/api/questions/'
SECTIONS_URL = '/api/questions/sections/'


def create_questions(sections: int, questions_per_section: int = 2):
    """Заполняет справочник: один тип, несколько разделов с вопросами."""
    question_type = QuestionType.objects.create(type='FAQ')
    for section_number in range(sections):
        section = QuestionSection.objects.create(
            section=f'Раздел {section_number}', type=question_type
        )
        for question_number in range(questions_per_section):
            Question.objects.create(
                question=f'Вопрос {section_number}-{question_number}',
                answer='Ответ',
                section=section,
            )
    return question_type


class QuestionsPaginationTest(TestCase):
    """Списки отдаются постранично."""

    def setUp(self):
        self.client = APIClient()

    def test_all_questions_is_paginated(self):
        """Разделы с вопросами приходят страницами по 10"""
        create_questions(sections=12)
        data = self.client.get(ALL_QUESTIONS_URL).json()
        self.assertEqual(data['count'], 12)
        self.assertEqual(data['page_size'], 10)
        self.assertEqual(data['pages_total'], 2)
        self.assertEqual(len(data['results']), 10)

    def test_second_page_returns_the_rest(self):
        """На второй странице лежат оставшиеся разделы"""
        create_questions(sections=12)
        data = self.client.get(ALL_QUESTIONS_URL, {'page': 2}).json()
        self.assertEqual(len(data['results']), 2)
        self.assertIsNone(data['next'])

    def test_page_size_can_be_changed(self):
        """page_size меняет размер страницы"""
        create_questions(sections=5)
        data = self.client.get(ALL_QUESTIONS_URL, {'page_size': 2}).json()
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['pages_total'], 3)

    def test_page_size_above_limit_is_rejected(self):
        """page_size больше максимума даёт 400"""
        create_questions(sections=1)
        response = self.client.get(ALL_QUESTIONS_URL, {'page_size': 1000})
        self.assertEqual(response.status_code, 400)

    def test_sections_list_is_paginated(self):
        """Список типов вопросов тоже постраничный"""
        create_questions(sections=2)
        data = self.client.get(SECTIONS_URL).json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['results']), 1)


class QuestionsQueryCountTest(TestCase):
    """Число запросов в базу не зависит от объёма справочника."""

    def setUp(self):
        self.client = APIClient()

    def test_all_questions_query_count_is_constant(self):
        """Разделы, вопросы и документы собираются фиксированным числом запросов"""
        create_questions(sections=3)
        with self.assertNumQueries(4):
            self.client.get(ALL_QUESTIONS_URL)

        Question.objects.all().delete()
        QuestionSection.objects.all().delete()
        QuestionType.objects.all().delete()
        create_questions(sections=9)
        with self.assertNumQueries(4):
            self.client.get(ALL_QUESTIONS_URL)

    def test_section_detail_query_count_is_constant(self):
        """Один раздел тоже собирается фиксированным числом запросов"""
        create_questions(sections=1, questions_per_section=5)
        section = QuestionSection.objects.first()
        with self.assertNumQueries(3):
            self.client.get(f'/api/questions/sections/{section.id}')
