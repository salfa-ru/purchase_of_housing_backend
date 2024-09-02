from django.urls import path

from questions.apps import QuestionsConfig
from questions.views import QuestionSectionListAPIView, QuestionSectionRetrieveAPIView

app_name = QuestionsConfig.name

urlpatterns = [
    path('sections/', QuestionSectionListAPIView.as_view(), name='sections'),
    path('sections/<pk>', QuestionSectionRetrieveAPIView.as_view(), name='questions'),
]