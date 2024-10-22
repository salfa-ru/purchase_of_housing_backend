from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Realty, Sale, Rent


class SaleInline(admin.StackedInline):
    model = Sale
    extra = 0


class RentInline(admin.StackedInline):
    model = Rent
    extra = 0


@admin.register(Realty)
class RealtyAdmin(admin.ModelAdmin):
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
    readonly_fields = ('id',)

    def get_readonly_fields(self, request, obj=None):
        """Делаем все поля, кроме 'realty_status', только для чтения при редактировании"""
        if obj:
            return [f.name for f in obj._meta.fields if f.name != 'realty_status'] + list(self.readonly_fields)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Логика проверки изменения статуса"""
        if change:
            old_instance = Realty.objects.get(pk=obj.pk)

            if old_instance.realty_status.status == 'На модерации':
                if obj.realty_status.status not in ['Активно', 'Отклонено']:
                    raise ValidationError("Статус можно изменить только на 'Активно' или 'Отклонено'.")
            elif old_instance.realty_status.status == 'Активно':
                if obj.realty_status.status != 'Отклонено':
                    raise ValidationError("Статус можно изменить только на 'Отклонено', если он 'Активно'.")
            elif old_instance.realty_status.status == 'Отклонено':
                raise ValidationError("Статус уже 'Отклонено' и не может быть изменен.")

        super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        """Перемещаем 'id' наверх."""
        fieldsets = super().get_fieldsets(request, obj)
        # Преобразуем fieldsets в список кортежей, чтобы добавить 'id'
        fieldsets = [(None, {'fields': ('id',)})] + list(fieldsets)
        return fieldsets

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
