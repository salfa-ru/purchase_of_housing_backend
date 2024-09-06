from django.db import models

from config.constants import CHAR_LENGTH, QUESTION_LENGTH


class QuestionType(models.Model):
    """Question Type model."""

    type = models.CharField(max_length=CHAR_LENGTH, verbose_name='Тип вопроса')

    class Meta:
        verbose_name = 'Тип вопроса'
        verbose_name_plural = 'Типы вопросов'

    def __str__(self):
        return self.type


class QuestionSection(models.Model):
    """Question Type model."""

    section = models.CharField(max_length=CHAR_LENGTH, verbose_name='Раздел')
    type = models.ForeignKey(
        QuestionType,
        on_delete=models.PROTECT, verbose_name='Тип вопроса', related_name='sections',
    )

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'

    def __str__(self):
        return self.section


class Question(models.Model):
    """Question model."""
    question = models.CharField(max_length=QUESTION_LENGTH, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')
    section = models.ForeignKey(
        QuestionSection,
        on_delete=models.PROTECT, verbose_name='Раздел', related_name='questions',
    )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return (f'{self.question[:20]}'
                f'{"..." if len(self.question) > 20 else ""}')


class DocumentTemplate(models.Model):
    """Document Template model."""
    title = models.CharField(max_length=CHAR_LENGTH, verbose_name='Название')
    document = models.FileField(upload_to='questions/documents', verbose_name='Документ')
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT, verbose_name='Вопрос', related_name='document_templates',
    )

    class Meta:
        verbose_name = 'Шаблон документа'
        verbose_name_plural = 'Шаблоны документов'

    def __str__(self):
        return f'{self.title} --- {self.document.name}'
