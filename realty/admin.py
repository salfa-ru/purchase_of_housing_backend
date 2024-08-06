from django.contrib import admin

from realty.models import Realty


# вариант для разработки (отображение и редактирование всех полей)
# TODO нужно настроить админку для prod-a
@admin.register(Realty)
class RealtyAdmin(admin.ModelAdmin):
    # TODO добавить город в адрес, когда поправим таблицы
    list_display = ('apartment', 'address_short', 'owner', 'owner_type', 'trade_type', 'realty_status', 'changed_at')
    list_filter = ('realty_status', 'trade_type', 'owner_type',)

    def apartment(self, obj):
        return (f'{obj.about_apartment.number_of_rooms.number_of_rooms}'
                f'{"-комн." if len(obj.about_apartment.number_of_rooms.number_of_rooms) <= 2 else ""} '
                f'{obj.realty_type.type}, '
                f'{obj.about_apartment.area} м², '
                f'{obj.about_apartment.floor}/{obj.about_apartment.floors_number} этаж')

    def address_short(self, obj):
        return (f'{obj.address.street.name}, '
                f'{obj.address.house_number}'
                f'{"копр." + obj.address.corpus if obj.address.corpus else ""}'
                f'{"стр." + obj.address.building if obj.address.building else ""}'
                f'{"вл." + obj.address.ownership if obj.address.ownership else ""}')

    apartment.short_description = 'Квартира'
    address_short.short_description = 'Адрес'
