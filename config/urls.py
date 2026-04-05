from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularSwaggerView, SpectacularRedocView, SpectacularAPIView
)
from drf_spectacular.utils import extend_schema
from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter

from users.views import CookieTokenObtainPairView, CookieTokenRefreshView
from .settings import DEBUG

# ========== Роутер для djoser с отдельным тегом ==========
router_djoser = DefaultRouter()
router_djoser.include_root_view = False  # ← убираем /auth/ и /users/
router_djoser.register(r'users', UserViewSet, basename='user')

# Применяем тег 'auth (djoser)' ко всем эндпоинтам djoser
for url in router_djoser.urls:
    if hasattr(url.callback, 'cls'):
        url.callback.cls = extend_schema(tags=['auth (djoser)'])(url.callback.cls)

urlpatterns = [
                  # Приложения
                  path('realty/', include('realty.urls')),
                  path('admin/', admin.site.urls),
                  path('users/', include('users.urls', namespace='users')),
                  path('questions/', include('questions.urls', namespace='questions')),
                  path('notifications/', include('notifications.urls', namespace='notifications')),
                  path('chats/', include('chats.urls', namespace='chats')),
                  path('realty-addresses/', include('realty_addresses.urls', namespace='realty-addresses')),
                  path('complaints/', include('complaints.urls', namespace='complaints')),
                  path('favorites/', include('favorites.urls', namespace='favorites')),

                  # Блок 'auth' — только токены
                  path('auth/token-auth/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('auth/token-refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),

                  # Блок 'auth (djoser)' — всё от djoser
                  path('auth/', include(router_djoser.urls)),

                  # Документация
                  path('schema/', SpectacularAPIView.as_view(), name='schema'),
                  path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
                  path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
                  path('hidden-health/', lambda request: HttpResponse(status=200)),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if DEBUG:
#    urlpatterns += [
# path('token-auth/', views.obtain_auth_token)
# path('token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),  # Use the custom view
#    ]

# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
#     )
