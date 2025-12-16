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

    # Проверка не просматривает ли пользователь свое объявление
    current_user = request.user
    if realty.owner_id == current_user.id:
        return

    # Получаем или создаем новый счетчик (ищем по дате, если она передана)
    if date:
        try:
            counter, created = model.objects.get_or_create(realty=realty, date=date)
        except model.MultipleObjectsReturned:
            # Handle duplicates gracefully - get the first one and clean up
            counter = model.objects.filter(realty=realty, date=date).first()
            # Delete other duplicates
            model.objects.filter(realty=realty, date=date).exclude(id=counter.id).delete()
    else:
        try:
            counter, created = model.objects.get_or_create(realty=realty)
        except model.MultipleObjectsReturned:
            # Handle duplicates gracefully - get the first one and clean up
            counter = model.objects.filter(realty=realty).first()
            # Delete other duplicates
            model.objects.filter(realty=realty).exclude(id=counter.id).delete()

    is_unique = is_unique_view(request, realty.id, timeout, key)

    if is_unique:
        counter.count = F('count') + 1
        counter.save()

    return
