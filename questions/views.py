from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from questions.models import QuestionSection, QuestionType
from questions.serializers import QuestionTypeSerializer, QuestionSectionFullSerializer


@extend_schema(summary='Получение списка "тип -> раздел -> вопросы"')
class QuestionSectionListAPIView(generics.ListAPIView):
    """Получение списка возможных разделов с входящими в них вопросами.
       Возможна фильтрация по типу вопросов: Правовая информация или FAQ."""
    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']


@extend_schema(summary='Получение списка "раздел -> (вопрос, ответ, документы)"')
class QuestionSectionRetrieveAPIView(generics.RetrieveAPIView):
    """Получение списка вопросов с ответами и файлами для заданного раздела"""
    queryset = QuestionSection.objects.all()
    serializer_class = QuestionSectionFullSerializer


# TODO - Если будет слишком много данных, нужен будет пагинатор!
@extend_schema(summary='Получение списка ВСЕХ разделов с вопросами, ответами и документами')
class AllQuestionsListAPIView(generics.ListAPIView):
    """Получение списка всех разделов с вопросами, ответами и документами"""
    queryset = QuestionSection.objects.all()
    serializer_class = QuestionSectionFullSerializer
