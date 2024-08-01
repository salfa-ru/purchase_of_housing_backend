from django.db import models

from config import constants


class City(models.Model):
    """City model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Город"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self):
        return f"Город: {self.name}"


class District(models.Model):
    """District model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Округ"
    )
    city = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.PROTECT,
        related_name="district",
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Округ"
        verbose_name_plural = "Округа"

    def __str__(self):
        return f"Округ: {self.name}, город: {self.city}"


class Zone(models.Model):
    """Zone model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Район"
    )
    district = models.ForeignKey(
        District,
        verbose_name="Округ",
        on_delete=models.PROTECT,
        related_name="zone",
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Район"
        verbose_name_plural = "Районы"

    def __str__(self):
        return f"Район: {self.name}, округ: {self.district}"


class Street(models.Model):
    """Street model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Улица"
    )
    zone = models.ForeignKey(
        Zone,
        verbose_name="Район",
        on_delete=models.PROTECT,
        related_name="street",
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Улица"
        verbose_name_plural = "Улицы"

    def __str__(self):
        return f"Улица: {self.name}, район: {self.zone}"


class Metro(models.Model):
    """Metro model."""

    name = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Метро"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Метро"
        verbose_name_plural = "Метро"

    def __str__(self):
        return f"Метро: {self.name}"


class House(models.Model):
    """House model."""

    street = models.ForeignKey(
        Street,
        verbose_name="Улица",
        on_delete=models.PROTECT,
        related_name="house",
    )
    house_number = models.PositiveSmallIntegerField(verbose_name="Номер дома")
    corpus = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Корпус", blank=True
    )
    building = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Строение", blank=True
    )
    ownership = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Владение", blank=True
    )
    map_point = models.CharField(
        max_length=constants.CHAR_LENGHT, verbose_name="Точка на карте"
    )
    metro = models.ForeignKey(
        Metro,
        verbose_name="Метро",
        on_delete=models.PROTECT,
        related_name="house",
    )
    minutes_to_metro = models.PositiveSmallIntegerField(
        verbose_name="Минут до метро"  # добавить валидацию на максимальное значение?
    )

    class Meta:
        ordering = ["street"]
        verbose_name = "Дом"
        verbose_name_plural = "Дома"

    def __str__(self):
        return (
            f"Улица: {self.street}, "
            f"Номер дома: {self.house_number}, "
            f"Корпус: {self.corpus}, "
            f"Строение: {self.building}, "
            f"Владение: {self.ownership}, "
            f"Точка на карте: {self.map_point}, "
            f"Метро: {self.metro}, "
            f"Минут до метро: {self.minutes_to_metro}, "
        )
