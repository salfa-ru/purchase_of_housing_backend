from django.contrib import admin

from .forms import RealtyForm
from .models import Realty, Sale, Rent


class SaleInline(admin.StackedInline):
    model = Sale
    extra = 0


class RentInline(admin.StackedInline):
    model = Rent
    extra = 0


@admin.register(Realty)
class RealtyAdmin(admin.ModelAdmin):
    form = RealtyForm
    list_display = ('id',
                    'apartment',
                    'address_short',
                    'owner',
                    'price',
                    'trade_type_short',
                    'realty_status',
                    'changed_at')
    list_display_links = ('id', 'apartment',)
    list_filter = ('realty_status',
                   'owner_type',)

    class Media:
        """ Отключение кнопок "Сохранить", если никаких изменений еще не внесено """
        js = ('js/disable_save_if_unchanged.js',)


    def get_readonly_fields(self, request, obj=None):
        """ Регулируем редактируемость полей для админа/модератора.
        Хотя в permissions модератор может менять realty, нужно, чтобы можно было менять только Статус """

        if request.user.is_superuser:
            # единственные read-only поля для админа:
            return ['id', 'changed_at']
        else:
            # для модератора - все поля read-only, кроме Статуса
            if obj:
                return [f.name for f in obj._meta.fields if f.name != 'realty_status'] + list(self.readonly_fields)
            return self.readonly_fields


    def get_fields(self, request, obj=None):
        """ Ставим ID и Статус сверху, дату редактирования в конце """

        # Получаем все поля
        fields = [f.name for f in Realty._meta.fields]

        # Убираем те, которые хотим разместить в определенном порядке, из текущего списка
        fields.remove('id')
        fields.remove('realty_status')
        fields.remove('changed_at')

        # Возвращаем поля в желаемом, удобном порядке
        return ['id', 'realty_status'] + fields + ['changed_at']


    def get_form(self, request, obj=None, **kwargs):
        """ Переписываю форму, чтобы в forms.py можно было узнать, какой пользователь сохранял объявление.
        Так Админ (но не Модератор) может менять в Realty все что угодно, включая статус БЕЗ ограничений! """

        form_class = super().get_form(request, obj, **kwargs)

        class FormWithRequest(form_class):
            def __init__(self, *args, **form_kwargs):
                form_kwargs['request'] = request
                super().__init__(*args, **form_kwargs)

        return FormWithRequest



    def apartment(self, obj):
        return (f'{obj.about_apartment.number_of_rooms.number_of_rooms}'
                f'{"-комн." if len(obj.about_apartment.number_of_rooms.number_of_rooms) <= 2 else ""} '
                f'{obj.realty_type.type}, '
                f'{obj.about_apartment.area} м.кв., '
                f'{obj.about_apartment.floor}/{obj.about_apartment.floors_number} этаж')

    def address_short(self, obj):
        return (
            f"{obj.address.street.name}, "
            f"{obj.address.house_number}"
            f'{"корп." + obj.address.corpus if obj.address.corpus else ""}'
            f'{"стр." + obj.address.building if obj.address.building else ""}'
            f'{"вл." + obj.address.ownership if obj.address.ownership else ""}'
        )

    def trade_type_short(self, obj):
        return obj.trade_type

    apartment.short_description = "Квартира"
    address_short.short_description = "Адрес"
    trade_type_short.short_description = "Тип сделки"

    def get_inlines(self, request, obj=None):
        """Использование inline формы только для уже созданной модели"""
        inlines = []
        if obj and obj.trade_type == "sale":
            inlines = [SaleInline]
        elif obj and obj.trade_type == "rent":
            inlines = [RentInline]
        return inlines


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'realty',
                    'sales_parameters',)
    list_display_links = ('realty',)
    readonly_fields = ('id',)


@admin.register(Rent)
class RentAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'realty',
                    'rental_features',
                    'lease_payments',)
    list_display_links = ('realty',)
    readonly_fields = ('id',)
