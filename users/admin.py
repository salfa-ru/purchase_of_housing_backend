from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'uuid_esa',)
    fields = [
        ('id', 'uuid_esa'),
        'username',
        ('first_name', 'last_name'),
        ('email', 'phone_number'),
        ('updated_at', 'date_joined'),
        'user_type',
        'avatar',
        'password',
        'is_superuser',
        'is_staff',
        'is_active',
        'groups',
        'user_permissions',
    ]

