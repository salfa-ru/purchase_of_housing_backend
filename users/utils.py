from datetime import datetime
import hashlib

from django.conf import settings

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


def hash_token(token):
    """Создает SHA-256 хеш токена."""
    if isinstance(token, str):
        token = token.encode('utf-8')
    return hashlib.sha256(token).hexdigest()


def set_jwt_cookies(request, response, refresh_token):
    """Устанавливает JWT токены в HttpOnly cookies."""

    # Для локальной разработки (http) отключаем Secure
    if settings.DEBUG and request.scheme == 'http':
        secure = False
    else:
        secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE']

    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=secure,
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    return response


def update_token_field(request, response):
    """Заменяет токен на хэш токена."""
    access_token = response.data.get('access')
    refresh_token = response.data.get('refresh')

    if refresh_token:
        refresh_token_hash = hash_token(refresh_token)
        # Получаем пользователя из refresh токена (через токен или request.user)
        user = request.user if request.user.is_authenticated else None

        # Если пользователь не определён, пробуем найти по токену
        if not user and refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            try:
                token = RefreshToken(refresh_token)
                user_id = token.get('user_id')
                from users.models import User
                user = User.objects.get(id=user_id)
            except Exception:
                pass

        if user:
            OutstandingToken.objects.filter(
                user=user,
                token=refresh_token
            ).update(token=refresh_token_hash)

    if access_token and refresh_token:
        response = set_jwt_cookies(request, response, refresh_token)

    return response


def delete_expired_tokens():
    """Удаляет записи устаревших хэшов токенов из базы данных."""
    expired_hash_tokens = OutstandingToken.objects.filter(
        expires_at__lt=datetime.now()
    )
    if expired_hash_tokens.exists():
        expired_hash_tokens.delete()
