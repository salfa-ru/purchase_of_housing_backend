from django.db import models

from config import constants


class BuildingType(models.Model):
    """Type of Building model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Тип дома"
    )

    class Meta:
        verbose_name = "Тип дома"
        verbose_name_plural = "Типы домов"

    def __str__(self):
        return f"{self.type}"


class RoomsNumber(models.Model):
    """Rooms Number model."""

    number_of_rooms = models.CharField(
        max_length=20, verbose_name="Количество комнат"
    )

    class Meta:
        verbose_name = "Количество комнат"
        verbose_name_plural = "Количество комнат"

    def __str__(self):
        return f"{self.number_of_rooms}"


class RepairType(models.Model):
    """Repair Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Тип ремонта"
    )

    class Meta:
        verbose_name = "Тип ремонта"
        verbose_name_plural = "Типы ремонта"

    def __str__(self):
        return f"{self.type}"


class CommunicationMethod(models.Model):
    """Communication Method model."""

    method = models.CharField(
        max_length=constants.CHAR_LENGTH, verbose_name="Способ связи"
    )

    class Meta:
        verbose_name = "Способ связи"
        verbose_name_plural = "Способы связи"

    def __str__(self):
        return f"{self.method}"


class RealtyAdvStatus(models.Model):
    """Realty Advertisment Status model."""

    status = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Статус объявления",
    )

    class Meta:
        verbose_name = "Статус объявления"
        verbose_name_plural = "Статусы объявлений"

    def __str__(self):
        return f"{self.status}"


class HousingType(models.Model):
    """Housing Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Тип жилья",
        default="Вторичное жилье",
    )

    class Meta:
        verbose_name = "Тип жилья"
        verbose_name_plural = "Типы жилья"

    def __str__(self):
        return f"{self.type}"


class SaleType(models.Model):
    """Sale Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Тип продажи",
        default="Свободная продажа",
    )

    class Meta:
        verbose_name = "Тип продажи"
        verbose_name_plural = "Типы продажи"

    def __str__(self):
        return f"{self.type}"


class TradeParticipant(models.Model):
    """Tade Participant model."""

    participant = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Участник сделки",
    )

    class Meta:
        verbose_name = "Участник сделки"
        verbose_name_plural = "Участники сделок"

    def __str__(self):
        return f"{self.participant}"


class RealtyType(models.Model):
    """Realty Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Тип недвижимости",
    )
    is_commercial = models.BooleanField(
        default=False,
        verbose_name="Коммерческая недвижимость"
    )

    class Meta:
        verbose_name = "Тип недвижимости"
        verbose_name_plural = "Типы недвижимости"

    def __str__(self):
        return f"{self.type}"


class BathroomType(models.Model):
    """Bathroom Type model."""

    type = models.CharField(
        max_length=constants.CHAR_LENGTH,
        verbose_name="Тип санузла",
    )

    class Meta:
        verbose_name = "Тип санузла"
        verbose_name_plural = "Типы санузлов"

    def __str__(self):
        return f"{self.type}"
