from django.contrib import admin

from notifications import models


@admin.register(models.NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'part1',
        'part2',
    )


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'user_to',
        'realty',
        'created_at',
        'is_new',
    )
    list_filter = (
        'template',
        'is_new',
    )


@admin.register(models.DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'platform',
        'created_at',
        'updated_at',
    )
    list_filter = ('platform',)
    search_fields = ('token', 'user__username')
