from django.db import models
from django.core import validators
from config import constants

from realty_values import models as md


class AboutBuilding(models.Model):
    """About Building model."""

    year_built = models.PositiveSmallIntegerField(
        verbose_name="Год постройки",
        validators=[
            validators.MinValueValidator(constants.MIN_YEAR_BUILT),
            validators.MaxValueValidator(constants.CURRENT_YEAR),
        ],
        blank=True,
    )
    type = models.ForeignKey(
        md.BuildingType,
        on_delete=models.PROTECT,
        verbose_name="Тип дома",
        related_name="about_house",
        blank=True,
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
        md.RoomsNumber,
        on_delete=models.PROTECT,
        verbose_name="Кол-во комнат",
        related_name="about_apartment",
    )
    area = models.FloatField(
        verbose_name="Площадь квартиры кв.м.",
        validators=[
            validators.MinValueValidator(constants.MIN_ROOM_AREA),
            validators.MaxValueValidator(constants.MAX_ROOM_AREA),
        ],
    )
    loggia = models.BooleanField(verbose_name="Лоджия", blank=True)
    balcony = models.BooleanField(verbose_name="Балкон", blank=True)
    elevator = models.BooleanField(verbose_name="Лифт", blank=True)

    class Meta:
        ordering = ["number_of_rooms"]
        verbose_name = "О квартире"
        verbose_name_plural = "О квартирах"

    def __str__(self):
        return (
            f"Кол-во комнат: {self.number_of_rooms}, Площадь: {self.area}, "
            f"Лоджия: {self.loggia}, Балкон: {self.balcony}, "
            f"Лифт: {self.elevator}"
        )


class CommonCharacteristics(models.Model):
    """Common Charcteristics model."""

    repair_type = models.ForeignKey(
        md.RepairType,
        on_delete=models.PROTECT,
        verbose_name="Тип ремонта",
        related_name="common_characteristics",
        blank=True,
    )
    furniture = models.BooleanField(blank=True, verbose_name="Мебель")
    courtyard_view = models.BooleanField(
        blank=True, verbose_name="Вид во двор"
    )
    street_view = models.BooleanField(blank=True, verbose_name="Вид на улицу")

    class Meta:
        ordering = ["repair_type"]
        verbose_name = "Общие характеристики"
        verbose_name_plural = "Общие характеристики"

    def __str__(self):
        return (
            f"Тип ремонта: {self.repair_type}, "
            f"Мебель: {self.furniture}, "
            f"Вид на двор: {self.courtyard_view}, "
            f"Вид на улицу: {self.street_view}"
        )


class RentalFeatures(models.Model):
    """Rental Features model."""

    fridge = models.BooleanField(verbose_name="Холодильник", blank=True)
    internet = models.BooleanField(verbose_name="Интернет", blank=True)
    conditioner = models.BooleanField(verbose_name="Кондиционер", blank=True)
    tv = models.BooleanField(verbose_name="Телевизор", blank=True)
    dishwasher = models.BooleanField(
        verbose_name="Посудомоечная машина", blank=True
    )
    washing_machine = models.BooleanField(
        verbose_name="Стиральная машина", blank=True
    )
    garbage_chute = models.BooleanField(
        verbose_name="Мусоропровод", blank=True
    )
    kids_allowed = models.BooleanField(
        verbose_name="Можно с детьми", blank=True
    )
    animals_allowed = models.BooleanField(
        verbose_name="Можно с животными", blank=True
    )

    class Meta:
        ordering = ["internet"]
        verbose_name = "Особенности аренды"
        verbose_name_plural = "Особенности аренды"

    def __str__(self):
        return (
            f"Холодильник: {self.fridge}, "
            f"Интернет: {self.internet}, "
            f"Кондиционер: {self.conditioner}, "
            f"Телевизор: {self.tv}, "
            f"Посудомоеяная машина: {self.internet}, "
            f"Стиральная машина: {self.conditioner}, "
            f"Мусоропровод: {self.tv}, "
            f"Можно с детьми: {self.tv}, "
            f"Можно с животными: {self.fridge}, "
        )


class LeasePayments(models.Model):
    """Lease Payment model."""

    counters_payment = models.ForeignKey(
        md.TradeParticipant,
        on_delete=models.PROTECT,
        blank=True,
        verbose_name="Оплата счетчиков",
        related_name="lease_payment_communal",
    )
    communal_payment = models.ForeignKey(
        md.TradeParticipant,
        on_delete=models.PROTECT,
        blank=True,
        verbose_name="Оплата ЖКХ",
        related_name="lease_payment_counters",
    )
    deposit = models.PositiveIntegerField(verbose_name="Залог", blank=True)

    class Meta:
        ordering = ["deposit"]
        verbose_name = "Платежи аренды"
        verbose_name_plural = "Платежи аренды"

    def __str__(self):
        return (
            f"Оплата счетчиков: {self.counters_payment}, "
            f"Оплата ЖКХ: {self.communal_payment}, "
        )


class SalesParameters(models.Model):
    """Sales Parameters model."""

    housing_type = models.ForeignKey(
        md.HousingType,
        on_delete=models.PROTECT,
        verbose_name="Тип жилья",
        related_name="sales_parameters",
    )
    sale_type = models.ForeignKey(
        md.SaleType,
        on_delete=models.PROTECT,
        verbose_name="Тип продажи",
        related_name="sales_parameters",
    )

    class Meta:
        ordering = ["housing_type"]
        verbose_name = "Параметры продажи"
        verbose_name_plural = "Параметры продаж"

    def __str__(self):
        return (
            f"Тип жилья: {self.housing_type}, "
            f"Тип продажи: {self.sale_type}, "
        )
