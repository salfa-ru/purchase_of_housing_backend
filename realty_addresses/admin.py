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
    )
    list_filter = ("name",)


@admin.register(models.Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )
    list_filter = ("name",)


@admin.register(models.Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "zone",
        "district",
        "city",

    )
    list_filter = ("name",)


@admin.register(models.Metro)
class MetroAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "house_number",
        "street",
        "corpus",
        "building",
        "ownership",
        "latitude",
        "longitude",
        "metro",
        "minutes_to_metro",
    )
    list_filter = ("street",)
