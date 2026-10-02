"""Отправка пуш-уведомлений через Firebase Cloud Messaging."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_user_tokens(user):
    """Токены всех устройств пользователя."""
    return list(user.device_tokens.values_list('token', flat=True))


def send_push(user, title, body='', data=None):
    """
    Отправляет пуш на все устройства пользователя."""
    tokens = get_user_tokens(user)

    if not tokens:
        logger.debug('push пропущен: у пользователя %s нет устройств', user.id)
        return 0

    if not settings.FIREBASE_ENABLED:
        logger.info(
            'push (заглушка): user=%s устройств=%d title=%r body=%r data=%r',
            user.id,
            len(tokens),
            title,
            body,
            data,
        )
        return 0

    try:
        return _send_via_fcm(tokens, title, body, data)
    except Exception:
        logger.exception('push не отправлен: неожиданная ошибка отправки')
        return 0


def _send_via_fcm(tokens, title, body, data):
    """Реальная отправка. Импорт внутри функции: без пакета сборка не ломается."""
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        logger.warning(
            'push не отправлен: FIREBASE_ENABLED=True, но firebase-admin не установлен'
        )
        return 0

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            )

        response = messaging.send_each_for_multicast(
            messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={key: str(value) for key, value in (data or {}).items()},
                tokens=tokens,
            )
        )
    except Exception:
        logger.exception('push не отправлен: ошибка обращения к FCM')
        return 0

    logger.info(
        'push отправлен: успешно=%d ошибок=%d',
        response.success_count,
        response.failure_count,
    )
    return response.success_count
