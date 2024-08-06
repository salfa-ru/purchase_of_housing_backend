from django.contrib import admin

from realty_addresses import models


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
    )
    list_filter = ("name",)


@admin.register(models.Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "district",
    )
    list_filter = ("name",)


@admin.register(models.Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "zone",
    )
    list_filter = ("name",)


@admin.register(models.Metro)
class MetroAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


@admin.register(models.House)
class HouseAdmin(admin.ModelAdmin):
    list_display = (
        "street",
        "house_number",
        "corpus",
        "building",
        "ownership",
        "map_point",
        "metro",
        "minutes_to_metro",
    )
    list_filter = ("street",)
