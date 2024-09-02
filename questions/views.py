from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from questions.models import QuestionSection, QuestionType
from questions.serializers import QuestionTypeSerializer, QuestionSectionFullSerializer


class QuestionSectionListAPIView(generics.ListAPIView):
    """Получение списка возможных разделов с входящими в них вопросами.
    Возможна фильтрация по типу вопросов: Правовая информация или FAQ."""
    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']


class QuestionSectionRetrieveAPIView(generics.RetrieveAPIView):
    """Получение списка вопросов с ответами и файлами для заданного раздела"""
    queryset = QuestionSection.objects.all()
    serializer_class = QuestionSectionFullSerializer
