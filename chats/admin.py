from django.contrib import admin
from django.forms import ModelForm
from django.urls import reverse
from django.utils.html import format_html

from chats.models import Blocking, Chat, Message


class MessageAdminForm(ModelForm):
    """Переопределенная форма, ограничивающая выбор отправителя в сообщениях
    --- Отправитель нового сообщения - его создатель
    --- Запрещено (не суперюзеру) менять отправителя"""

    class Meta:
        model = Message
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and not self.request.user.is_superuser:
            if self.instance.pk:
                self.fields['user_from'].queryset = self.fields[
                    'user_from'
                ].queryset.filter(id=self.instance.user_from.id)
                self.fields['user_from'].help_text = (
                    'У существующего сообщения отправителя менять нельзя.<br>'
                    "<span style='color: red;'>"
                    'Хмм, а остальное, получается, можно? </span>'
                )

            else:
                self.fields['user_from'].queryset = self.fields[
                    'user_from'
                ].queryset.filter(id=self.request.user.id)
                self.fields['user_from'].initial = self.request.user
                self.fields[
                    'user_from'
                ].help_text = 'Новое сообщение можно создать только от своего имени.'

            self.fields['user_from'].empty_label = None


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'msg_id',
        'str_link',
        'user_from',
        'user_to',
        'sender_is_owner',
        'created_at',
        'is_new',
        'read_at',
        'is_deleted_from',
        'is_deleted_to',
    )
    list_filter = ('chat', 'user_from', 'user_to', 'created_at', 'is_new')

    form = MessageAdminForm

    def str_link(self, obj):
        """Кликабельная ссылка на страницу редактирования объекта."""
        url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk]
        )
        return format_html('<a href="{}">{}</a>', url, str(obj))

    str_link.short_description = 'Сообщение'
    str_link.admin_order_field = '__str__'

    def get_form(self, request, obj=None, **kwargs):
        admin_form = super().get_form(request, obj, **kwargs)

        class AdminFormWithRequest(admin_form):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return admin_form(*args, **kwargs)

        return AdminFormWithRequest

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'user_from' in fields:
            fields = ('user_from',) + tuple(f for f in fields if f != 'user_from')
        return fields


@admin.register(Blocking)
class BlockingAdmin(admin.ModelAdmin):
    list_display = (
        'user_who',
        'user_whom',
    )
    list_filter = ('user_who', 'user_whom')
    search_fields = ('user_who__username', 'user_whom__username')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'realty', 'owner', 'client')
    list_filter = ('owner', 'client')
    search_fields = ('realty__address', 'owner__username', 'client__username')
