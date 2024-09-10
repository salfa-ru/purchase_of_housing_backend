from django.db import models

from users import models as user_models
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty_addresses import models as addresses_models
from config.constants import DESCRIPTION_LENGTH, NULLABLE_FIELD


class Realty(models.Model):
    """Base Realty model."""

    owner = models.ForeignKey(
        user_models.User,
        on_delete=models.PROTECT,
        verbose_name="Владелец",
        related_name="realty",
    )
    realty_type = models.ForeignKey(
        values_models.RealtyType,
        on_delete=models.PROTECT,
        verbose_name="Тип недвижимости",
        related_name="realty",
    )
    address = models.ForeignKey(
        addresses_models.Address,
        on_delete=models.PROTECT,
        verbose_name="Адрес",
        related_name="realty",
    )
    about_building = models.ForeignKey(
        specificities_models.AboutBuilding,
        on_delete=models.PROTECT,
        verbose_name="О доме",
        related_name="realty",
        **NULLABLE_FIELD,
    )
    about_apartment = models.ForeignKey(
        specificities_models.AboutApartment,
        on_delete=models.PROTECT,
        verbose_name="О квартире",
        related_name="realty",
    )
    common_characteristics = models.ForeignKey(
        specificities_models.CommonCharacteristics,
        on_delete=models.PROTECT,
        verbose_name="Общие характеристики",
        related_name="realty",
        **NULLABLE_FIELD,
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        verbose_name="Описание",
    )
    price = models.PositiveIntegerField(
        verbose_name="Цена",
    )
    commission = models.PositiveIntegerField(
        verbose_name="Комиссия",
        **NULLABLE_FIELD,
    )
    owner_type = models.ForeignKey(
        values_models.TradeParticipant,
        on_delete=models.PROTECT,
        verbose_name="Тип владельца",
        related_name="realty",
    )
    communication_method = models.ForeignKey(
        values_models.CommunicationMethod,
        on_delete=models.PROTECT,
        verbose_name="Способ связи",
        related_name="realty",
    )
    realty_status = models.ForeignKey(
        values_models.RealtyAdvStatus,
        on_delete=models.PROTECT,
        verbose_name="Статус",
        related_name="realty",
    )
    published_at = models.DateTimeField(
        default=None,
        verbose_name="Дата и время публикации",
        **NULLABLE_FIELD,
    )
    changed_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Последнее изменение",
    )

    @property
    def trade_type(self):
        if hasattr(self, "sale_profile"):
            return "sale"
        if hasattr(self, "rent_profile"):
            return "rent"
        return "unknown"

    class Meta:
        verbose_name = "Недвижимость"
        verbose_name_plural = "Недвижимость"

    def __str__(self):
        return (
            f"{self.about_apartment.number_of_rooms.number_of_rooms}"
            f'{"-комн." if len(self.about_apartment.number_of_rooms.number_of_rooms) <= 2 else ""} '
            f"{self.realty_type.type}, "
            f"{self.about_apartment.area} м², "
            f"{self.about_apartment.floor}/{self.about_apartment.floors_number} этаж --- "
            f"{self.address.street.name}, "
            f"{self.address.house_number}"
            f'{"копр." + self.address.corpus if self.address.corpus else ""}'
            f'{"стр." + self.address.building if self.address.building else ""}'
            f'{"вл." + self.address.ownership if self.address.ownership else ""} --- '
            f"{self.owner.username}--"
            f"{self.realty_status}"
        )
        # TODO переделать пользователя, когда будет кастомный пользователь


class Sale(models.Model):
    """Sale Realty model."""
    realty = models.OneToOneField(
        Realty,
        on_delete=models.CASCADE,
        related_name='sale_profile',
    )
    sales_parameters = models.ForeignKey(
        specificities_models.SalesParameters,
        on_delete=models.PROTECT,
        verbose_name="Параметры продажи",
        related_name="sales",
    )

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"


class Rent(models.Model):
    """Rent Realty model."""
    realty = models.OneToOneField(
        Realty,
        on_delete=models.CASCADE,
        related_name='rent_profile',
    )
    rental_features = models.ForeignKey(
        specificities_models.RentalFeatures,
        on_delete=models.PROTECT,
        verbose_name="Особенности аренды",
        related_name="rents",
        **NULLABLE_FIELD,
    )
    lease_payments = models.ForeignKey(
        specificities_models.LeasePayments,
        on_delete=models.PROTECT,
        verbose_name="Платежи аренды",
        related_name="rents",
        **NULLABLE_FIELD,
    )

    class Meta:
        verbose_name = "Аренда"
        verbose_name_plural = "Аренда"
