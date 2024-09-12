from django.db import models
from django.core import validators
from config import constants

from realty_values import models as values_models


class AboutBuilding(models.Model):
    """About Building model."""

    year_built = models.PositiveSmallIntegerField(
        verbose_name="Год постройки",
        validators=[
            validators.MinValueValidator(constants.MIN_YEAR_BUILT),
            validators.MaxValueValidator(constants.CURRENT_YEAR),
        ],
        **constants.NULLABLE_FIELD,
    )
    type = models.ForeignKey(
        values_models.BuildingType,
        on_delete=models.PROTECT,
        verbose_name="Тип дома",
        related_name="about_houses",
        **constants.NULLABLE_FIELD,
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "О доме"
        verbose_name_plural = "О домах"

    def __str__(self):
        return (
            f"Здание построено в {self.year_built}, "
            f"тип строения - {self.type}"
        )


class AboutApartment(models.Model):
    """About Apartment model."""

    number_of_rooms = models.ForeignKey(
        values_models.RoomsNumber,
        on_delete=models.PROTECT,
        verbose_name="Кол-во комнат",
        related_name="about_apartments",
    )
    area = models.FloatField(
        verbose_name="Площадь квартиры кв.м.",
        validators=[
            validators.MinValueValidator(constants.MIN_ROOM_AREA),
            validators.MaxValueValidator(constants.MAX_ROOM_AREA),
        ],
    )
    loggia = models.BooleanField(verbose_name="Лоджия", default=False)
    balcony = models.BooleanField(verbose_name="Балкон", default=False)
    elevator = models.BooleanField(verbose_name="Лифт", default=False)
    floor = models.PositiveSmallIntegerField(
        verbose_name="Этаж", default=False
    )
    floors_number = models.PositiveSmallIntegerField(
        verbose_name="Этажность", default=False
    )

    class Meta:
        ordering = ["number_of_rooms"]
        verbose_name = "О квартире"
        verbose_name_plural = "О квартирах"

    def __str__(self):
        characteristics = [f"{self.number_of_rooms} комн., {self.area} кв.м"]

        if self.loggia:
            characteristics.append("Лоджия")
        if self.balcony:
            characteristics.append("Балкон")
        if self.elevator:
            characteristics.append("Лифт")

        characteristics.append(f"Этаж: {self.floor}/{self.floors_number}")
        return ", ".join(characteristics)


class CommonCharacteristics(models.Model):
    """Common Charcteristics model."""

    repair_type = models.ForeignKey(
        values_models.RepairType,
        on_delete=models.PROTECT,
        verbose_name="Тип ремонта",
        related_name="common_characteristics",
        **constants.NULLABLE_FIELD,
    )
    furniture = models.BooleanField(verbose_name="Мебель", default=False)
    bathroom = models.ForeignKey(
        values_models.BathroomType,
        on_delete=models.PROTECT,
        verbose_name="Тип санузла",
        related_name="common_characteristics",
        **constants.NULLABLE_FIELD,
    )
    courtyard_view = models.BooleanField(verbose_name="Вид во двор")
    street_view = models.BooleanField(verbose_name="Вид на улицу")

    class Meta:
        ordering = ["repair_type"]
        verbose_name = "Общие характеристики"
        verbose_name_plural = "Общие характеристики"

    def __str__(self):
        characteristics = []

        if self.repair_type:
            characteristics.append(f"Тип ремонта: {self.repair_type}")
        if self.furniture:
            characteristics.append("Мебель")
        if self.bathroom:
            characteristics.append(f"Тип санузла: {self.bathroom}")
        if self.courtyard_view:
            characteristics.append("Вид во двор")
        if self.street_view:
            characteristics.append("Вид на улицу")

        return (
            ", ".join(characteristics)
            if characteristics
            else "Нет общих характеристик"
        )


class RentalFeatures(models.Model):
    """Rental Features model."""

    fridge = models.BooleanField(verbose_name="Холодильник", default=False)
    internet = models.BooleanField(verbose_name="Интернет", default=False)
    conditioner = models.BooleanField(
        verbose_name="Кондиционер", default=False
    )
    tv = models.BooleanField(verbose_name="Телевизор", default=False)
    dishwasher = models.BooleanField(
        verbose_name="Посудомоечная машина", default=False
    )
    washing_machine = models.BooleanField(
        verbose_name="Стиральная машина", default=False
    )
    garbage_chute = models.BooleanField(
        verbose_name="Мусоропровод", default=False
    )
    kids_allowed = models.BooleanField(
        verbose_name="Можно с детьми", default=False
    )
    animals_allowed = models.BooleanField(
        verbose_name="Можно с животными", default=False
    )

    class Meta:
        ordering = ["internet"]
        verbose_name = "Особенности аренды"
        verbose_name_plural = "Особенности аренды"

    def __str__(self):
        features = []
        if self.fridge:
            features.append("Холодильник")
        if self.internet:
            features.append("Интернет")
        if self.conditioner:
            features.append("Кондиционер")
        if self.tv:
            features.append("Телевизор")
        if self.dishwasher:
            features.append("Посудомоечная машина")
        if self.washing_machine:
            features.append("Стиральная машина")
        if self.garbage_chute:
            features.append("Мусоропровод")
        if self.kids_allowed:
            features.append("Можно с детьми")
        if self.animals_allowed:
            features.append("Можно с животными")

        return ", ".join(features) if features else "Нет особенностей"


class LeasePayments(models.Model):
    """Lease Payment model."""

    counters_payment = models.ForeignKey(
        values_models.TradeParticipant,
        on_delete=models.PROTECT,
        **constants.NULLABLE_FIELD,
        verbose_name="Оплата счетчиков",
        related_name="lease_payments_communal",
    )
    communal_payment = models.ForeignKey(
        values_models.TradeParticipant,
        on_delete=models.PROTECT,
        **constants.NULLABLE_FIELD,
        verbose_name="Оплата ЖКХ",
        related_name="lease_payments_counters",
    )
    deposit = models.PositiveIntegerField(
        verbose_name="Залог", **constants.NULLABLE_FIELD
    )

    class Meta:
        ordering = ["deposit"]
        verbose_name = "Платежи аренды"
        verbose_name_plural = "Платежи аренды"

    def __str__(self):
        return (
            f"{self.counters_payment}, "
            f"{self.communal_payment}, "
            f"{self.deposit}"
        )


class SalesParameters(models.Model):
    """Sales Parameters model."""

    housing_type = models.ForeignKey(
        values_models.HousingType,
        on_delete=models.PROTECT,
        verbose_name="Тип жилья",
        related_name="sales_parameters",
    )
    sale_type = models.ForeignKey(
        values_models.SaleType,
        on_delete=models.PROTECT,
        verbose_name="Тип продажи",
        related_name="sales_parameters",
    )

    class Meta:
        ordering = ["housing_type"]
        verbose_name = "Параметры продажи"
        verbose_name_plural = "Параметры продаж"

    def __str__(self):
        return f"{self.housing_type}, {self.sale_type}"
