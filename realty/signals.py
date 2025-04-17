from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from django_q.tasks import Schedule

from realty.models import Realty
# from realty_values import models as values_models
from notifications.utils import create_notification

from config.constants import MAX_LISTING_DURATION

# TODO - Вопрос о целесообразности использования сигналов:

""" Из документации Django:  SIGNALS CAN MAKE YOUR CODE HARDER TO MAINTAIN. 
Consider implementing a helper method on a custom manager, to both update your models 
and perform additional logic, or else overriding model methods before using model signals"""

# TODO - Сохранение объявления - ДОБАВИТЬ ОПОВЕЩЕНИЕ ДЛЯ УДАЛЕНИЯ ОБЪЯВЛЕНИЯ


@receiver(pre_save, sender=Realty)
def handle_realty_save(sender, instance, **kwargs):
    """ Обработка сохранения объявления:
    - установка статуса "на модерации" новому объявлению
    - создание уведомлений при смене статусов
    - создание задач для django q2 на деактивацию объявлений """

    if hasattr(instance, '_pre_save_in_progress'):
        return  # Предотвращаем рекурсию

    instance._pre_save_in_progress = True  # Устанавливаем флаг

    is_new = instance.id is None

    if is_new:

        """ 
        Логика перенесена в serializers - во избежание двойного сохранения записи 
        # Новое объявление - устанавливаем статус 'На модерации'
        instance.realty_status = values_models.RealtyAdvStatus.objects.get(id=2)
        instance.save()  # Сохраняем, чтобы получить id
        create_notification(instance, "on_moderation")
        """
        return

    else:
        # Старое объявление - узнаем старый статус
        try:
            old_instance = Realty.objects.get(id=instance.id)

        except Realty.DoesNotExist:
            # TODO - Надо ли ставить задачи на деактивации объявлений из loaddata data.json?
            # Похоже, тут обрабатывается добавление новых объявлений из loaddata data.json
            # Поэтому выходим из этого сигнала, не обрабатывая такие записи
            return

        # old_instance = Realty.objects.get(id=instance.id)  # перенесено в try - выше
        old_status = old_instance.realty_status
        new_status = instance.realty_status

        old_is_deleted = old_instance.is_deleted
        new_is_deleted = instance.is_deleted

        if old_is_deleted != new_is_deleted and new_is_deleted is True:
            create_notification(instance, "deleted")
            Schedule.objects.filter(func="realty.tasks.expire_realty", args=instance.id).delete()
            print("Deleted, sent message to Host about it")

        ...

        if new_status != old_status:

            """ СОЗДАНИЕ ИЛИ УДАЛЕНИЕ ЗАДАЧ НА ДЕАКТИВАЦИЮ ОБЪЯВЛЕНИЯ"""

            # Объявление Активировано
            if new_status.id == 1:
                instance.published_at = timezone.now()  # Выставляем время активации`
                instance.save()

                # Планируем время деактивации (создаем запись в таблице Django_Q)
                Schedule.objects.create(
                    func="realty.tasks.expire_realty",
                    name=f"Deactivation of Realty #{instance.id}",
                    args=instance.id,  # записываем туда id объявления
                    schedule_type=Schedule.ONCE,
                    next_run=timezone.now() + MAX_LISTING_DURATION
                )

            # Объявление Деактивировано
            elif old_status and old_status.id == 1:
                instance.published_at = None

                # Удаляем запланированную деактивацию из Django_Q,
                # иначе объявление, активированное еще раз, отключится по старому графику
                Schedule.objects.filter(func="realty.tasks.expire_realty", args=instance.id).delete()

            print(f"DEBUG - realty/signals.py - handle_realty_save() - @pre_save")
            print(f"        Статус realty #{instance.id}: '{old_status.status}' --> '{new_status.status}'.")

            """ ОТПРАВКА УВЕДОМЛЕНИЙ """

            if new_status.id == 1:  # стало Активно
                create_notification(instance, "published")

            elif new_status.id == 2:  # ушло на Модерацию
                create_notification(instance, "on_moderation")

            elif new_status.id == 3:      # ОТКЛОНЕНО:
                if old_status.id == 1:    # было активно, но заблокировано Админом
                    create_notification(instance, "blocked")
                elif old_status.id == 2:  # было на модерации, но отклонено Админом
                    create_notification(instance, "rejected")

            """ НОВОЕ - Перенесено в Архив из Модерации"""
            if new_status.id == 4:  # стало в Архиве
                if old_status.id == 2:  # было на Модерации
                    create_notification(instance, "archived")

            """ ВНИМАНИЕ! Уведомления о переносе АКТИВНЫХ объявлений В АРХИВ 
            отправляются только при истечении срока публикации деактивирующей функцией из tasks.py. 
            При ручном переносе объявлений в архив уведомления не отправляются. 
            elif new_status.id == 4:
                create_notification(instance, "expired")
            """


""" Статусы realty          Типы нотификаций  (16/10/2024) """
# 1 - Активно               2 published
# 2 - На модерации          1 on_moderation
# 3 - Отклонено             3 rejected
# 4 - В архиве              4 expired
# 5 - ЧЕРНОВИК (нет)        5 blocked
#                           6 archived
