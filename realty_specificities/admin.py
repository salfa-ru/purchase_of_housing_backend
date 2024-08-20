from django.contrib import admin

from realty_specificities import models


@admin.register(models.AboutBuilding)
class AboutBuildingAdmin(admin.ModelAdmin):
    list_display = ("year_built", "type")
    list_filter = ("type",)


@admin.register(models.AboutApartment)
class AboutApartmentAdmin(admin.ModelAdmin):
    list_display = ("number_of_rooms", "area", "loggia", "balcony", "elevator", "floor", "floors_number",)
    list_filter = ("number_of_rooms",)


@admin.register(models.CommonCharacteristics)
class CommonCharacteristicsAdmin(admin.ModelAdmin):
    list_display = (
        "repair_type",
        "furniture",
        "bathroom",
        "courtyard_view",
        "street_view",
    )
    list_filter = ("repair_type",)


@admin.register(models.RentalFeatures)
class RentalFeaturesAdmin(admin.ModelAdmin):
    list_display = (
        "fridge",
        "internet",
        "conditioner",
        "tv",
        "dishwasher",
        "washing_machine",
        "garbage_chute",
        "kids_allowed",
        "animals_allowed",
    )
    list_filter = ("internet",)


@admin.register(models.LeasePayments)
class LeasePaymentssAdmin(admin.ModelAdmin):
    list_display = (
        "counters_payment",
        "communal_payment",
        "deposit",
    )
    list_filter = ("deposit",)


@admin.register(models.SalesParameters)
class SalesParameterssAdmin(admin.ModelAdmin):
    list_display = (
        "housing_type",
        "sale_type",
    )
    list_filter = ("housing_type",)
