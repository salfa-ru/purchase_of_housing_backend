from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

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
            f"{self.about_apartment.area} м.кв., "
            f"{self.about_apartment.floor}/{self.about_apartment.floors_number} этаж --- "
            f"{self.address.street.name}, "
            f"{self.address.house_number}"
            f'{"копр." + self.address.corpus if self.address.corpus else ""}'
            f'{"стр." + self.address.building if self.address.building else ""}'
            f'{"вл." + self.address.ownership if self.address.ownership else ""} --- '
            f"{self.owner.username}"
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


# TODO - Перенести обработку сигналов в signals.py ?
# TODO - Вопрос о целесообразности использования сигналов:

""" Из документации Django: Signals can make your code harder to maintain. 
Consider implementing a helper method on a custom manager, to both update your models 
and perform additional logic, or else overriding model methods before using model signals"""


@receiver(pre_save, sender=Realty)
def handle_realty_save(sender, instance, **kwargs):
    """ Обработка сохранения объявления:
    - установка статуса "на модерации" новому объявлению
    - создание уведомлений при смене статусов """

    if hasattr(instance, '_pre_save_in_progress'):
        return  # Предотвращаем рекурсию

    from notifications.utils import create_notification

    instance._pre_save_in_progress = True  # Устанавливаем флаг

    is_new = instance.id is None

    if is_new:
        # Новое объявление - устанавливаем статус 'На модерации'
        instance.realty_status = values_models.RealtyAdvStatus.objects.get(id=2)
        instance.save()  # Сохраняем, чтобы получить id
        create_notification(instance, "on_moderation")

    else:
        # Старое объявление - узнаем старый статус
        old_instance = Realty.objects.get(id=instance.id)
        old_status = old_instance.realty_status
        new_status = instance.realty_status

        if new_status != old_status:
            # print(f"Статус realty #{instance.id} "
            #       f"изменился с '{old_status.status}' на '{new_status.status}'.")

            if new_status.id == 1:
                create_notification(instance, "published")
            elif new_status.id == 2:
                create_notification(instance, "on_moderation")
            elif new_status.id == 3:
                create_notification(instance, "rejected")
            elif new_status.id == 4:
                create_notification(instance, "expired")

            # Статуса для заблокированного объявления пока нет, есть только Нотификация "blocked"
            # elif new_status.id == 5:
            #    create_notification(instance, "blocked")


""" Статусы realty  ---   Типы нотификаций  (16/10/2024) """
# 1 - Активно       ---   2 published      <----  жалко, что id
# 2 - На модерации  ---   1 on_moderation  <----  не совпадают
# 3 - Отклонено     ---   3 rejected
# 4 - В архиве      ---   4 expired
# 5 - xxxxxxxx      ---   5 blocked   <---------  В таблице пока нет такого статуса
