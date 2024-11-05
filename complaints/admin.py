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
        if obj is None:
            return ('owner', 'realty', 'description')
        return ('display_owner', 'display_realty', 'description')

    def has_change_permission(self, request, obj=None):
        return obj is None

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj is not None else []

    def has_add_permission(self, request):
        return True
