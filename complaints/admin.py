from django.contrib import admin

from complaints import models


@admin.register(models.Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('get_short_description', 'owner_name', 'realty_name', 'is_new',)
    list_filter = ('is_new',)
    readonly_fields = ('owner_name', 'realty_name', 'description',)
    fields = ('owner_name', 'realty_name', 'description',)

    def get_short_description(self, obj):
        return (f'{obj.description[:20]}'
                f'{"..." if len(obj.description) > 20 else ""}')

    get_short_description.short_description = 'Жалоба'

    def realty_name(self, obj):
        return str(obj.realty)

    realty_name.short_description = 'Объявление'

    def owner_name(self, obj):
        return str(obj.owner)

    owner_name.short_description = 'Владелец жалобы'

    def has_change_permission(self, request, obj=None):
        return obj is None

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj is not None else []
