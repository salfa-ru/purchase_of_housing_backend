from django.urls import path

from questions.apps import QuestionsConfig
from questions.views import (
    AllQuestionsListAPIView,
    QuestionSectionListAPIView,
    QuestionSectionRetrieveAPIView,
)

app_name = QuestionsConfig.name

urlpatterns = [
    path('sections/', QuestionSectionListAPIView.as_view(), name='sections'),
    path('sections/<pk>', QuestionSectionRetrieveAPIView.as_view(), name='questions'),
    # новый эндпойт который показывает все вопросы и ответы сразу
    path('', AllQuestionsListAPIView.as_view(), name='all_questions'),
]
