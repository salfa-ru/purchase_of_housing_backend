from django.contrib import admin

from realty_displays import models


@admin.register(models.DisplayInSearch)
class DisplayInSearchAdmin(admin.ModelAdmin):
    list_display = ('count', 'realty', 'realty_id',)
    list_display_links = ('count',)

    def realty_id(self, obj):
        """Returns the realty ID."""
        return obj.realty.pk if obj.realty else None
    realty_id.short_description = 'ID недвижимости'
    realty_id.admin_order_field = 'realty__id'


@admin.register(models.DisplayFullInfo)
class DisplayFullInfoAdmin(admin.ModelAdmin):
    list_display = ('date', 'count', 'realty', 'realty_id',)
    list_display_links = ('date', 'count',)

    def realty_id(self, obj):
        """Returns the realty ID."""
        return obj.realty.pk if obj.realty else None
    realty_id.short_description = 'ID недвижимости'
    realty_id.admin_order_field = 'realty__id'
