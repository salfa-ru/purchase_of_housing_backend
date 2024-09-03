from django.contrib import admin
from django.utils.safestring import mark_safe

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'uuid_esa', 'preview_avatar', 'preview_phone_qr_code',)
    fields = [
        ('id', 'uuid_esa'),
        'username',
        ('first_name', 'last_name'),
        ('email', 'phone_number'),
        ('preview_phone_qr_code', 'phone_qr_code'),
        ('updated_at', 'date_joined'),
        'user_type',
        ('preview_avatar', 'avatar'),
        'password',
        'is_superuser',
        'is_staff',
        'is_active',
        'groups',
        'user_permissions',
    ]

    def preview_avatar(self, obj):
        return mark_safe(f'<img src="{obj.avatar.url}" style="width: 100px">')

    def preview_phone_qr_code(self, obj):
        return mark_safe(f'<img src="{obj.phone_qr_code.url}" style="width: 100px">')

    preview_avatar.short_description = 'Превью'
    preview_phone_qr_code.short_description = 'Превью'
