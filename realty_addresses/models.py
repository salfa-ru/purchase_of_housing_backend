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
    city = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.PROTECT,
        related_name="districts",
        **constants.NULLABLE_FIELD,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Округ"
        verbose_name_plural = "Округа"

    def __str__(self):
        return f"{self.name}, {self.city}"


class Zone(models.Model):
    """Zone model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Район"
    )
    district = models.ForeignKey(
        District,
        verbose_name="Округ",
        on_delete=models.PROTECT,
        related_name="zones",
        **constants.NULLABLE_FIELD,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Район"
        verbose_name_plural = "Районы"

    def __str__(self):
        return f"{self.name}, {self.district}"


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

    class Meta:
        ordering = ["name"]
        verbose_name = "Улица"
        verbose_name_plural = "Улицы"

    def __str__(self):
        return f"{self.name}, {self.zone}"


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


class House(models.Model):
    """House model."""

    street = models.ForeignKey(
        Street,
        verbose_name="Улица",
        on_delete=models.PROTECT,
        related_name="houses",
    )
    house_number = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Номер дома"
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
        related_name="houses",
        **constants.NULLABLE_FIELD,
    )
    minutes_to_metro = models.PositiveSmallIntegerField(
        verbose_name="Минут до метро",  # добавить валидацию на максимальное значение?
        **constants.NULLABLE_FIELD,
    )

    class Meta:
        ordering = ["street"]
        verbose_name = "Дом"
        verbose_name_plural = "Дома"

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
