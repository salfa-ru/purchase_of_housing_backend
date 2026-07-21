from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class CookieJWTAuthentication(JWTAuthentication):
    """Аутентификация через access token в заголовке или cookie с проверкой черного списка."""

    def authenticate(self, request):
        # 1. Проверяем заголовок Authorization
        header = self.get_header(request)
        if header:
            raw_token = self.get_raw_token(header)
            if raw_token:
                try:
                    validated_token = AccessToken(raw_token)
                    # Проверка черного списка
                    if BlacklistedToken.objects.filter(
                        token__jti=validated_token['jti']
                    ).exists():
                        raise AuthenticationFailed('Token is blacklisted')
                    user = self.get_user(validated_token)
                    return user, validated_token
                except Exception:
                    return None

        # 2. Проверяем cookie
        raw_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        )
        if raw_token:
            try:
                validated_token = AccessToken(raw_token)
                # Проверка черного списка
                if BlacklistedToken.objects.filter(
                    token__jti=validated_token['jti']
                ).exists():
                    raise AuthenticationFailed('Token is blacklisted')
                user = self.get_user(validated_token)
                return user, validated_token
            except Exception:
                return None

        # 3. Если нигде нет токена — возвращаем None
        return None

    def get_user(self, validated_token):
        try:
            user_id = validated_token.payload.get(
                settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id')
            )
            if user_id is None:
                raise AuthenticationFailed('User ID claim not found')
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
