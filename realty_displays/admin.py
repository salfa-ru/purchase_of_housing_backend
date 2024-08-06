from django.contrib import admin

from realty_displays import models

@admin.register(models.DisplayInSearch)
class DisplayInSearchAdmin(admin.ModelAdmin):
    list_display = ('date', 'count', 'realty',)
    list_display_links = ('date', 'count',)


@admin.register(models.DisplayFullInfo)
class DisplayInSearchAdmin(admin.ModelAdmin):
    list_display = ('count', 'realty',)
    list_display_links = ('count',)
