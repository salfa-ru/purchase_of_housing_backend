from django.contrib import admin

from complaints import models


@admin.register(models.Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('get_short_description', 'display_owner', 'display_realty', 'is_new',)
    list_filter = ('is_new',)
    readonly_fields = ('display_owner', 'display_realty', 'description',)

    def get_short_description(self, obj):
        return (f'{obj.description[:20]}'
                f'{"..." if len(obj.description) > 20 else ""}')

    get_short_description.short_description = 'Жалоба'

    def display_realty(self, obj):
        return str(obj.realty)

    display_realty.short_description = 'Объявление'

    def display_owner(self, obj):
        return str(obj.owner)

    display_owner.short_description = 'Владелец жалобы'

    def get_fields(self, request, obj=None):
        # Если объект еще не сохранен, показываем все поля для создания
        if obj is None:
            return ('owner', 'realty', 'description', 'is_new')
        # Для существующих объектов поле 'is_new' должно быть доступно для редактирования
        return ('display_owner', 'display_realty', 'description', 'is_new')

    def get_readonly_fields(self, request, obj=None):
        # Если объект уже создан, делаем все поля, кроме 'is_new', только для чтения
        return self.readonly_fields if obj is None else self.readonly_fields

    def has_add_permission(self, request):
        return True
