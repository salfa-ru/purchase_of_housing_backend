from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics

from questions.models import QuestionSection, QuestionType
from questions.serializers import QuestionSectionFullSerializer, QuestionTypeSerializer


@extend_schema(
    tags=['Вопросы'],
    summary='Получение списка "тип -> раздел -> вопросы"',
    description='Возвращает все разделы с вопросами. Можно отфильтровать по типу вопроса.',
    parameters=[
        OpenApiParameter(
            name='type',
            description='Тип вопроса. Доступные значения: FAQ, Правовая информация и другие, созданные в админке.',
            required=False,
            type=str,
            examples=[
                OpenApiExample('FAQ', value='FAQ'),
                OpenApiExample('Правовая информация', value='Правовая информация'),
            ],
        ),
    ],
)
class QuestionSectionListAPIView(generics.ListAPIView):
    """Получение списка возможных разделов с входящими в них вопросами.
    Возможна фильтрация по типу вопросов: Правовая информация или FAQ."""

    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']


@extend_schema(
    tags=['Вопросы'],
    summary='Получение списка "раздел -> (вопрос, ответ, документы)"',
    description='Возвращает все вопросы, ответы и документы для указанного раздела.',
    parameters=[
        OpenApiParameter(
            name='id',
            description='ID раздела',
            required=True,
            type=int,
        ),
    ],
)
class QuestionSectionRetrieveAPIView(generics.RetrieveAPIView):
    """Получение списка вопросов с ответами и файлами для заданного раздела"""

    queryset = QuestionSection.objects.all()
    serializer_class = QuestionSectionFullSerializer


# TODO - Если будет слишком много данных, нужен будет пагинатор!
@extend_schema(
    tags=['Вопросы'],
    summary='Получение списка ВСЕХ разделов с вопросами, ответами и документами',
)
class AllQuestionsListAPIView(generics.ListAPIView):
    """Получение списка всех разделов с вопросами, ответами и документами"""

    queryset = QuestionSection.objects.all()
    serializer_class = QuestionSectionFullSerializer
