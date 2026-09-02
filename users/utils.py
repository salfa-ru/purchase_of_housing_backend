import hashlib
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


def hash_token(token):
    """Создает SHA-256 хеш токена."""
    if isinstance(token, str):
        token = token.encode('utf-8')
    return hashlib.sha256(token).hexdigest()


def set_jwt_cookies(request, response, refresh_token):
    """Устанавливает JWT токены в HttpOnly cookies."""
    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    return response


def clear_jwt_cookies(response):
    """Удаляет refresh-куки."""
    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value='',
        max_age=0,
        expires='Thu, 01 Jan 1970 00:00:00 GMT',
        httponly=True,
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    return response


def update_token_field(request, response):
    """
    Обновляет токены: хэширует refresh, устанавливает cookie.
    """
    access_token = response.data.get('access')
    refresh_token = response.data.get('refresh')

    # 🔧 ДОБАВЛЯЕМ: сохраняем access токен
    if access_token:
        try:
            access_token_obj = AccessToken(access_token)
            jti = access_token_obj['jti']
            user_id = access_token_obj['user_id']
            expires_at = datetime.fromtimestamp(access_token_obj['exp'])

            OutstandingToken.objects.get_or_create(
                jti=jti,
                defaults={
                    'user_id': user_id,
                    'token': access_token,
                    'expires_at': expires_at,
                },
            )
        except Exception:
            pass

    # Обрабатываем refresh токен
    if refresh_token:
        refresh_token_hash = hash_token(refresh_token)
        refresh_token_obj = RefreshToken(refresh_token)

        try:
            username = request.data.get('username')
            user_id = User.objects.get(username=username).id
        except (User.DoesNotExist, AttributeError):
            user_id = refresh_token_obj.payload.get(api_settings.USER_ID_CLAIM, None)

        if user_id:
            jti = refresh_token_obj.payload.get('jti')
            expires_at = datetime.fromtimestamp(refresh_token_obj.payload.get('exp'))

            OutstandingToken.objects.get_or_create(
                jti=jti,
                defaults={
                    'user_id': user_id,
                    'token': refresh_token,
                    'expires_at': expires_at,
                },
            )
            OutstandingToken.objects.filter(
                user_id=user_id, token=refresh_token
            ).update(token=refresh_token_hash)

        if access_token and refresh_token:
            response = set_jwt_cookies(request, response, refresh_token)

    # Убираем refresh из тела ответа
    if 'refresh' in response.data:
        del response.data['refresh']

    return response


def delete_expired_tokens():
    """Удаляет записи устаревших хэшов токенов из базы данных."""
    expired_hash_tokens = OutstandingToken.objects.filter(expires_at__lt=datetime.now())
    if expired_hash_tokens.exists():
        expired_hash_tokens.delete()
