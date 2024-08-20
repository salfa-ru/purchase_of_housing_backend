from django.contrib import admin

from realty_values import models


@admin.register(models.BuildingType)
class BuildinTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)


@admin.register(models.RoomsNumber)
class RoomsNumberAdmin(admin.ModelAdmin):
    list_display = ("number_of_rooms",)
    list_filter = ("number_of_rooms",)


@admin.register(models.RepairType)
class RepairTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)


@admin.register(models.CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("method",)
    list_filter = ("method",)


@admin.register(models.RealtyAdvStatus)
class RealtyAdvStatusAdmin(admin.ModelAdmin):
    list_display = ("status",)
    list_filter = ("status",)


@admin.register(models.HousingType)
class HousingTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)


@admin.register(models.SaleType)
class SaleTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)


@admin.register(models.TradeParticipant)
class TradeParticipantAdmin(admin.ModelAdmin):
    list_display = ("participant",)
    list_filter = ("participant",)


@admin.register(models.RealtyType)
class RealtyTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)


@admin.register(models.BathroomType)
class BathroomTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)
    list_filter = ("type",)
