from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

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

    # По-человечески можно выбирать группы и права для пользователей.
    filter_horizontal = ('groups', 'user_permissions',)

    def preview_avatar(self, obj):
        return mark_safe(f'<img src="{obj.avatar.url}" style="width: 100px">')

    def preview_phone_qr_code(self, obj):
        return mark_safe(f'<img src="{obj.phone_qr_code.url}" style="width: 100px">')

    preview_avatar.short_description = 'Превью'
    preview_phone_qr_code.short_description = 'Превью'


# Удаляем Group из стандартной админки
admin.site.unregister(Group)


# Переопределяем Group, чтобы она была частью "users"
class CustomGroup(Group):
    class Meta:
        proxy = True  # Делаем прокси-модель
        app_label = "users"  # Переносим в приложение users
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


@admin.register(CustomGroup)
class CustomGroupAdmin(GroupAdmin):
    pass