from django.contrib import admin
from django.utils.safestring import mark_safe

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'uuid_esa', 'preview',)
    fields = [
        ('id', 'uuid_esa'),
        'username',
        ('first_name', 'last_name'),
        ('email', 'phone_number'),
        ('updated_at', 'date_joined'),
        'user_type',
        ('preview', 'avatar'),
        'password',
        'is_superuser',
        'is_staff',
        'is_active',
        'groups',
        'user_permissions',
    ]

    def preview(self, obj):
        return mark_safe(f'<img src="{obj.avatar.url}" style="width: 100px">')

    preview.short_description = 'Превью'
