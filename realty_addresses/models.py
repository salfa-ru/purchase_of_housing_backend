from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from config import constants


class City(models.Model):
    """City model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Город"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self):
        return f"{self.name}"


class District(models.Model):
    """District model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Округ"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Округ"
        verbose_name_plural = "Округа"

    def __str__(self):
        return f"{self.name}"


class Zone(models.Model):
    """Zone model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Район"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Район"
        verbose_name_plural = "Районы"

    def __str__(self):
        return f"{self.name}"


class Street(models.Model):
    """Street model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Улица"
    )
    zone = models.ForeignKey(
        Zone,
        verbose_name="Район",
        on_delete=models.PROTECT,
        related_name="streets",
        **constants.NULLABLE_FIELD,
    )
    district = models.ForeignKey(
        District,
        verbose_name="Округ",
        on_delete=models.PROTECT,
        related_name="streets",
        **constants.NULLABLE_FIELD,
    )
    city = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.PROTECT,
        related_name="streets",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Улица"
        verbose_name_plural = "Улицы"

    def __str__(self):
        return f"{self.name}, {self.zone}, {self.district}, {self.city}"


class Metro(models.Model):
    """Metro model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Метро"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Метро"
        verbose_name_plural = "Метро"

    def __str__(self):
        return f"{self.name}"


class Address(models.Model):
    """Address model."""

    house_number = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Номер дома"
    )
    street = models.ForeignKey(
        Street,
        verbose_name="Улица",
        on_delete=models.PROTECT,
        related_name="addresses",
    )
    corpus = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Корпус",
        **constants.NULLABLE_FIELD,
    )
    building = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Строение",
        **constants.NULLABLE_FIELD,
    )
    ownership = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Владение",
        **constants.NULLABLE_FIELD,
    )
    map_point = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Точка на карте"
    )
    metro = models.ForeignKey(
        Metro,
        verbose_name="Метро",
        on_delete=models.PROTECT,
        related_name="addresses",
        **constants.NULLABLE_FIELD,
    )
    minutes_to_metro = models.PositiveSmallIntegerField(
        verbose_name="Минут до метро",
        **constants.NULLABLE_FIELD,
        validators=[
            MinValueValidator(
                constants.MIN_TIME,
                message='Минимальное время не может быть меньше 1 минуты!'),
            MaxValueValidator(
                constants.MAX_TIME,
                message='Минимальное время не может быть больше 60 минут!'
            )
        ]
    )

    class Meta:
        ordering = ["street"]
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

    def __str__(self):
        return (
            f"{self.street}, "
            f"{self.house_number}, "
            f"{self.corpus}, "
            f"{self.building}, "
            f"{self.ownership}, "
            f"{self.map_point}, "
            f"{self.metro}, "
            f"{self.minutes_to_metro}"
        )
