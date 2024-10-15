from django.utils import timezone
from django.db.models import F


def is_unique_view(request, realty_id, timeout, key):
    session_key = f"{key}_{realty_id}"
    last_viewed = request.session.get(session_key)

    if last_viewed:
        try:
            last_viewed_time = timezone.datetime.fromisoformat(last_viewed)
            if timezone.now() - last_viewed_time < timeout:
                return False  # счетчик не трогаем, объявление показывалось недавно
        except (ValueError, TypeError):
            pass  # Если значение last_viewed некорректно, просто игнорируем

    # Обновить время последнего просмотра
    # Просмотр обновляется ДО внесения изменения в базу!
    request.session[session_key] = timezone.now().isoformat()
    return True


def increment_counter(request, realty, model, timeout, key, date=None):
    """Увеличение счетчика показа в поиске или в Full View"""

    # Получаем или создаем новый счетчик (ищем по дате, если она передана)
    if date:

        # Проверка не просматривает ли пользователь свое объявление
        current_user = request.user
        if realty.owner_id == current_user.id:
            return

        counter, created = model.objects.get_or_create(realty=realty, date=date)
    else:
        counter, created = model.objects.get_or_create(realty=realty)

    is_unique = is_unique_view(request, realty.id, timeout, key)

    if is_unique:
        counter.count = F('count') + 1
        counter.save()

    return
