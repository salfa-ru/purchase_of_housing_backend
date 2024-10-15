from django.contrib import admin

from questions import models


@admin.register(models.QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ('type',)


@admin.register(models.QuestionSection)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ('section', 'type',)
    list_filter = ('type',)


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'section', 'q_type')
    list_filter = ('section',)
    fields = ('question', 'answer', 'section', 'q_type',)
    readonly_fields = ('q_type',)

    def q_type(self, obj):
        return obj.section.type

    q_type.short_description = 'Тип'


@admin.register(models.DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'filename', 'question',)

    def filename(self, obj):
        return obj.document.name

    filename.short_description = 'Файл'
