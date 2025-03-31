from django.utils import timezone
from datetime import timedelta
from django_q.tasks import Schedule

from notifications.utils import create_notification
from realty.models import Realty
from realty_values import models as values_models

from config.constants import MAX_LISTING_DURATION


def plan_mass_deactivation():
    """ Во время запуска Django создает задачу ежечасной пакетной деактивации устаревших объявлений """
    now = timezone.now()
    next_hour = now + timedelta(hours=1)
    top_of_next_hour = next_hour.replace(minute=0, second=0, microsecond=0)

    # Удаляем старую запись, если есть
    Schedule.objects.filter(func="realty.tasks.expire_all_outdated_realties").delete()

    # Создаем новую такую - планируем время деактивации (создаем запись в таблице Django_Q)
    Schedule.objects.create(
        func="realty.tasks.expire_all_outdated_realties",
        name="Mass Deactivation - HOURLY",  # Название запланированной задачи
        schedule_type=Schedule.HOURLY,  # График выполнения
        next_run=top_of_next_hour
    )


def expire_realty(realty_id):
    """ Деактивирует одно запланированное объявление """

    print(f"DEBUG - realty/tasks.py - expire_realty(): ДЕАКТИВАЦИЯ Записи #{realty_id}")

    time_threshold = timezone.now() - MAX_LISTING_DURATION

    try:
        # realty = Realty.objects.get(id=realty_id)  # вариант без доп-проверок

        # тут с дополнительными проверками - деактивируем только те, что нужно, а не перевыставленные
        realty = Realty.objects.get(
            is_deleted=False,
            id=realty_id,
            realty_status=1,
            published_at__isnull=False,
            published_at__lte=time_threshold
        )

        expired_status = values_models.RealtyAdvStatus.objects.get(id=4)  # В архиве / expired
        realty.realty_status = expired_status

        realty.save()

    except Realty.DoesNotExist:
        print(f"------- ДЕАКТИВАЦИЯ Записи #{realty_id} НЕ УДАЛАСЬ!")
        print(f"        (запись уже удалена / не активна / выставлена еще раз)")
        return

    print(f"------- ЗАПИСЬ #{realty_id} успешно деактивирована!")
    create_notification(realty, "expired")


def expire_all_outdated_realties():
    """ Деактивирует все устаревшие объявления - HOURLY и при запуске DJANGO """
    expired_status = values_models.RealtyAdvStatus.objects.get(id=4)  # В архиве / expired
    time_threshold = timezone.now() - MAX_LISTING_DURATION

    outdated_realties = Realty.objects.filter(
        is_deleted=False,
        realty_status=1,
        published_at__isnull=False,
        published_at__lte=time_threshold
    )

    for realty in outdated_realties:
        realty.realty_status = expired_status
        realty.save()  # Запускаем pre-save-сигналы!

    """ Код ниже работает, но не вызывает сигналы к сожалению!
    updated_count = Realty.objects.filter(
        realty_status=1,
        published_at__isnull=False,
        published_at__lte=time_threshold
    ).update(realty_status=expired_status)  
    # updated_count можно было использовать в строке снизу """

    print(f"DEBUG - tasks.py - expire_all_outdated_realties(): "
          f"Деактивировано {outdated_realties.count()} объявлений.")
