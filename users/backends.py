import jwt
from rest_framework import exceptions
from rest_framework import authentication
from cryptography.hazmat.primitives import serialization

from config.constants import ConstantsAuth
from users.models import User
from users.services import create_user_from_esa, update_user_from_esa


class CustomAuthentication(authentication.BaseAuthentication):
    """Custom authenticate with ESA"""

    def authenticate(self, request):
        request.user = None

        auth_header = authentication.get_authorization_header(request).split()

        if not self._check_auth_header(auth_header):
            return None

        token = auth_header[1]

        token_data = self._get_token_data(token)

        user = self._get_user_by_id(token_data['user_id'], token)

        # TODO доделать когда появится дата
        # if user.changed_at != token_data.get('data'):
        #     update_user_from_esa(user, token)

        return (user, token)

    def authenticate_header(self, request):
        """Определяет заголовок WWW-Authenticate ответа при ошибке 401
        Без переопределения этого метода вместо 401 возвращается 403"""
        return ' '

    @staticmethod
    def _check_auth_header(auth_header):
        """Проверка header"""
        if not auth_header:
            return None
        elif len(auth_header) == 1:
            return None
        elif len(auth_header) > 2:
            return None
        elif auth_header[0] != ConstantsAuth.AUTH_HEADER_PREFIX:
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
        except jwt.InvalidTokenError as e:
            msg = f'Invalid token'
            raise exceptions.AuthenticationFailed(detail=msg)

        if not payload.get('user_id'):
            msg = 'Token does not contain user_id'
            raise exceptions.AuthenticationFailed(detail=msg)

        # TODO добавить дату, когда она появится в токене
        return {'user_id': payload.get('user_id')}

    @staticmethod
    def _get_user_by_id(user_id, token):
        if User.objects.filter(pk=user_id).exists():
            return User.objects.get(pk=user_id)
        return create_user_from_esa(user_id, token)
