from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """Аутентификация через access token в заголовке или cookie."""

    def authenticate(self, request):
        header = self.get_header(request)
        if header:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if not raw_token:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
