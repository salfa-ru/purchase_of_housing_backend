from django.contrib import admin

from .models import Realty, Sale, Rent


class SaleInline(admin.StackedInline):
    model = Sale
    extra = 0


class RentInline(admin.StackedInline):
    model = Rent
    extra = 0


@admin.register(Realty)
class RealtyAdmin(admin.ModelAdmin):
    list_display = ('apartment',
                    'address_short',
                    'owner',
                    'price',
                    'trade_type_short',
                    'realty_status',
                    'changed_at')
    list_filter = ('realty_status',
                   'owner_type',)

    def apartment(self, obj):
        return (f'{obj.about_apartment.number_of_rooms.number_of_rooms}'
                f'{"-комн." if len(obj.about_apartment.number_of_rooms.number_of_rooms) <= 2 else ""} '
                f'{obj.realty_type.type}, '
                f'{obj.about_apartment.area} м², '
                f'{obj.about_apartment.floor}/{obj.about_apartment.floors_number} этаж')

    def address_short(self, obj):
        return (f'{obj.address.street.name}, '
                f'{obj.address.house_number}'
                f'{"корп." + obj.address.corpus if obj.address.corpus else ""}'
                f'{"стр." + obj.address.building if obj.address.building else ""}'
                f'{"вл." + obj.address.ownership if obj.address.ownership else ""}')

    def trade_type_short(self, obj):
        return obj.trade_type

    apartment.short_description = 'Квартира'
    address_short.short_description = 'Адрес'
    trade_type_short.short_description = 'Тип сделки'

    def get_inlines(self, request, obj=None):
        """Использование inline формы только для уже созданной модели"""
        inlines = []
        if obj and obj.trade_type == 'sale':
            inlines = [SaleInline]
        elif obj and obj.trade_type == 'rent':
            inlines = [RentInline]
        return inlines


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('realty',
                    'sales_parameters',)


@admin.register(Rent)
class RentAdmin(admin.ModelAdmin):
    list_display = ('realty',
                    'rental_features',
                    'lease_payments',)
