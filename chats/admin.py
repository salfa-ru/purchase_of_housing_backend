from django.contrib import admin

from chats.models import Chat, Blocking

from django.forms import ModelForm


class ChatAdminForm(ModelForm):
    """ Переопределенная форма, ограничивающая выбор отправителя в сообщениях
    --- Отправитель нового сообщения - его создатель
    --- Запрещено (не суперюзеру) менять отправителя """

    class Meta:
        model = Chat
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)


        if self.request and not self.request.user.is_superuser:
            if self.instance.pk:  # Существующая запись - запрет на изменение отправителя!
                self.fields['user_from'].queryset = self.fields['user_from'].queryset.filter(
                    id=self.instance.user_from.id
                )
                self.fields['user_from'].help_text = ("У существующего сообщения отправителя менять нельзя.<br>"
                                                      "<span style='color: red;'>"
                                                      "Хмм, а остальное, получается, можно? </span>")

            else:  # Новая запись - автоматически выбирается текущий пользователь (модератор)
                self.fields['user_from'].queryset = self.fields['user_from'].queryset.filter(
                    id=self.request.user.id
                )
                self.fields['user_from'].initial = self.request.user
                self.fields['user_from'].help_text = "Новое сообщение можно создать только от своего имени."

            self.fields['user_from'].empty_label = None  # запрет на выбор ПУСТОГО отправителя


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'id',
        'user_from',
        'user_to',
        'is_new',
        'datetime',
        'is_deleted_from',
        'is_deleted_to',
        'datetime',
    )

    form = ChatAdminForm

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
