from django.db import models

from config import constants


class BuildingType(models.Model):
    """Type of Building model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Тип дома"
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "Тип дома"
        verbose_name_plural = "Типы домов"

    def __str__(self):
        return f"Тип строения - {self.type}"


class RoomsNumber(models.Model):
    """Rooms Number model."""

    number_of_rooms = models.CharField(
        max_length=20, verbose_name="Количество комнат"
    )

    class Meta:
        ordering = ["number_of_rooms"]
        verbose_name = "Количество комнат"
        verbose_name_plural = "Количество комнат"

    def __str__(self):
        return f"Количество комнат: {self.number_of_rooms}"


class RepairType(models.Model):
    """Repair Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Тип ремонта"
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "Тип ремонта"
        verbose_name_plural = "Типы ремонта"

    def __str__(self):
        return f"Тип ремонта - {self.type}"


class CommunicationMethod(models.Model):
    """Communication Method model."""

    method = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Способ связи"
    )

    class Meta:
        ordering = ["method"]
        verbose_name = "Способ связи"
        verbose_name_plural = "Способы связи"

    def __str__(self):
        return f"Способ связи - {self.method}"


class AdStatus(models.Model):
    """Advertisment Status model."""

    status = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Статус объявления"
    )

    class Meta:
        ordering = ["status"]
        verbose_name = "Статус объявления"
        verbose_name_plural = "Статусы объявлений"

    def __str__(self):
        return f"Статус объявления - {self.status}"


class HousingType(models.Model):
    """Housing Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Тип жилья",
        default="Вторичное жилье",
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "Тип жилья"
        verbose_name_plural = "Типы жилья"

    def __str__(self):
        return f"Тип жилья - {self.type}"


class SaleType(models.Model):
    """Sale Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Тип продажи",
        default="Свободная продажа",
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "Тип продажи"
        verbose_name_plural = "Типы продажи"

    def __str__(self):
        return f"Тип продажи - {self.type}"


class TradeParticipant(models.Model):
    """Tade Participant model."""

    participant = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Участник сделки",
    )

    class Meta:
        ordering = ["participant"]
        verbose_name = "Участник сделки"
        verbose_name_plural = "Участники сделок"

    def __str__(self):
        return f"Участник сделки - {self.participant}"


class TradeType(models.Model):
    """Trade Type model."""

    noun_type = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Тип сделки сущ.",
    )

    verb_type = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Тип сделки гл.",
    )

    class Meta:
        ordering = ["noun_type"]
        verbose_name = "Тип сделки"
        verbose_name_plural = "Типы сделок"

    def __str__(self):
        return (
            f"Тип сделки сущ. - {self.noun_type}, "
            f"Тип сделки гл. - {self.verb_type}, "
            )


class RealtyType(models.Model):
    """Realty Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGHT,
        verbose_name="Тип недвижимости",
    )

    class Meta:
        ordering = ["type"]
        verbose_name = "Тип недвижимости"
        verbose_name_plural = "Типы недвижимости"

    def __str__(self):
        return f"Тип недвижимости - {self.type}"
