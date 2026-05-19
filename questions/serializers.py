from rest_framework import serializers

from questions.models import DocumentTemplate, Question, QuestionSection, QuestionType


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Получение информации по документу"""

    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'title',
            'document',
        ]


class QuestionFullSerializer(serializers.ModelSerializer):
    """Получения полной информации по вопросу, включая файлы."""

    document_templates = DocumentTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'question',
            'answer',
            'document_templates',
        ]


class QuestionSectionFullSerializer(serializers.ModelSerializer):
    """Получение полной информации по всем вопросам в разделе"""

    questions = QuestionFullSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSection
        fields = [
            'id',
            'section',
            'questions',
        ]


class QuestionShortSerializer(serializers.ModelSerializer):
    """Получения списка вопросов.
    Используется внутри матрешки 'тип вопросов-разделы-список вопросов'"""

    class Meta:
        model = Question
        fields = [
            'id',
            'question',
        ]


class QuestionSectionShortSerializer(serializers.ModelSerializer):
    """Получения списка разделов со списком входящих в него вопросов.
    Используется внутри матрешки 'тип вопросов-разделы-список вопросов'"""

    questions = QuestionShortSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSection
        fields = [
            'id',
            'section',
            'questions',
        ]


class QuestionTypeSerializer(serializers.ModelSerializer):
    """Получение тип вопросов - входящие в него разделы - входящие в него вопросы."""

    sections = QuestionSectionShortSerializer(many=True)

    class Meta:
        model = QuestionType
        fields = [
            'id',
            'type',
            'sections',
        ]
