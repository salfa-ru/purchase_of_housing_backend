from django.contrib import admin

from chats.models import Chat

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'user_from',
        'user_to',
        'is_new',
        'datetime',
        'is_deleted_from',
        'is_deleted_to',
        'is_blocked_from',
        'is_blocked_to',
        'datetime',
    )
