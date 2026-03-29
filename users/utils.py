from datetime import datetime
import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


User = get_user_model()


def hash_token(token):
    """Создает SHA-256 хеш токена."""
    if isinstance(token, str):
        token = token.encode('utf-8')
    return hashlib.sha256(token).hexdigest()


def set_jwt_cookies(request, response, refresh_token):
    """Устанавливает JWT токены в HttpOnly cookies."""
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
    refresh_token_hash = hash_token(refresh_token)
    refresh_token_obj = RefreshToken(refresh_token)
    try:
        username = request.data.get('username')
        user_id = User.objects.get(username=username).id
    except:
        user_id = refresh_token_obj.payload.get(
            api_settings.USER_ID_CLAIM,
            None
        )
    OutstandingToken.objects.filter(
        user_id=user_id,
        token=refresh_token
    ).update(token=refresh_token_hash)
    if access_token and refresh_token:
        response = set_jwt_cookies(
            request,
            response,
            refresh_token
        )
    return response


def delete_expired_tokens():
    """Удаляет записи устаревших хэшов токенов из базы данных."""
    expired_hash_tokens = OutstandingToken.objects.filter(
        expires_at__lt=datetime.now()
    )
    if expired_hash_tokens.exists():
        expired_hash_tokens.delete()


#def check_refresh_token(refresh_token):
#    """Проверяет статус и срок действия refresh-токена."""
#    refresh_token_hash = hash_token(refresh_token)
#    refresh_token_id = OutstandingToken.objects.get(token=refresh_token_hash)
#    if BlacklistedToken.objects.get(token_id=refresh_token_id).id():
#        raise InvalidToken
    
