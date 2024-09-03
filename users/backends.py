from datetime import datetime

import jwt
from rest_framework import exceptions, authentication
from cryptography.hazmat.primitives import serialization

from config.constants import ConstantsAuth
from users.models import User
from users.services import create_user_from_esa, update_user_from_esa


class CustomAuthentication(authentication.BaseAuthentication):
    """Custom authenticate with ESA"""

    def authenticate(self, request):
        """
        Основной метод кастомной аутентификации.
        Получает заголовок Authorization, проверяет его сстав и наличие префикса.
        Декодирует токен, получает из него uuid пользователя и дату последнего изменения профиля.
        Получает пользователя по uuid (либо создает нового и сохраняет в базу).
        Обновляет пользователя в базе, если даты последнего изменения не совпадают.
        """

        request.user = None

        auth_header = authentication.get_authorization_header(request).split()

        if not self._check_auth_header(auth_header):
            return None

        token = auth_header[1]

        token_data = self._get_token_data(token)

        user = self._get_user_by_id(token_data['user_id'], token)

        if (token_data.get('updated_at') and
                user.updated_at.timestamp() != datetime.fromisoformat(token_data.get('updated_at')).timestamp()):
            update_user_from_esa(user, token)

        return user, token

    def authenticate_header(self, request):
        """Определяет заголовок WWW-Authenticate ответа при ошибке 401
        Без переопределения этого метода вместо 401 возвращается 403"""
        return 'jwt auth'

    @staticmethod
    def _check_auth_header(auth_header):
        """Проверка заголовок Authorization"""
        if (not auth_header
                or auth_header[0] != ConstantsAuth.AUTH_HEADER_PREFIX
                or len(auth_header) == 1
                or len(auth_header) > 2):
            return None
        return True

    @staticmethod
    def _get_token_data(token):
        """Проверка токена и получение данных их него
        (id пользователя и дата последнего изменения профиля)"""

        with open(ConstantsAuth.AUTH_KEY_PATH, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=ConstantsAuth.TOKEN_AUD,
            )
        except jwt.ExpiredSignatureError:
            msg = 'Token has expired'
            raise exceptions.AuthenticationFailed(detail=msg)
        except jwt.InvalidTokenError:
            msg = f'Invalid token'
            raise exceptions.AuthenticationFailed(detail=msg)

        if not payload.get(ConstantsAuth.PREFIX_USER_ID_IN_TOKEN):
            msg = 'Token does not contain user_id'
            raise exceptions.AuthenticationFailed(detail=msg)

        return {'user_id': payload.get(ConstantsAuth.PREFIX_USER_ID_IN_TOKEN),
                'updated_at': payload.get(ConstantsAuth.PREFIX_UPDATED_DATE_IN_TOKEN)}

    @staticmethod
    def _get_user_by_id(user_id, token):
        """Получает пользователя из базы или создает нового, если в базе такого не было."""
        if not User.objects.filter(uuid_esa=user_id).exists():
            create_user_from_esa(user_id, token)
        return User.objects.get(uuid_esa=user_id)
