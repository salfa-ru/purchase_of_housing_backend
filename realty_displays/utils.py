from django.db.models import F
from django.utils import timezone


def is_unique_view(request, realty_id, timeout, key):
    session_key = f'{key}_{realty_id}'
    last_viewed = request.session.get(session_key)

    if last_viewed:
        try:
            last_viewed_time = timezone.datetime.fromisoformat(last_viewed)
            if timezone.now() - last_viewed_time < timeout:
                return False
        except (ValueError, TypeError):
            pass

    request.session[session_key] = timezone.now().isoformat()
    return True


def increment_counter(request, realty, model, timeout, key, date=None):
    """Увеличение счетчика показа в поиске или в Full View"""

    current_user = request.user
    if realty.owner_id == current_user.id:
        return

    if date:
        try:
            counter, created = model.objects.get_or_create(realty=realty, date=date)
        except model.MultipleObjectsReturned:
            counter = model.objects.filter(realty=realty, date=date).first()
            model.objects.filter(realty=realty, date=date).exclude(
                id=counter.id
            ).delete()
    else:
        try:
            counter, created = model.objects.get_or_create(realty=realty)
        except model.MultipleObjectsReturned:
            counter = model.objects.filter(realty=realty).first()
            model.objects.filter(realty=realty).exclude(id=counter.id).delete()

    is_unique = is_unique_view(request, realty.id, timeout, key)

    if is_unique:
        counter.count = F('count') + 1
        counter.save()

    return
