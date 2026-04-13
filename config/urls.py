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
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from users.views import CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView
from .settings import DEBUG

# ========== Роутер для djoser с отдельным тегом ==========
router_djoser = DefaultRouter()
router_djoser.include_root_view = False
router_djoser.register(r'users', UserViewSet, basename='user')

for url in router_djoser.urls:
    if hasattr(url.callback, 'cls'):
        url.callback.cls = extend_schema(tags=['auth (djoser)'])(url.callback.cls)

urlpatterns = [
    path('api/realty/', include('realty.urls')),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/questions/', include('questions.urls', namespace='questions')),
    path('api/notifications/', include('notifications.urls', namespace='notifications')),
    path('api/chats/', include('chats.urls', namespace='chats')),
    path('api/realty-addresses/', include('realty_addresses.urls', namespace='realty-addresses')),
    path('api/complaints/', include('complaints.urls', namespace='complaints')),
    path('api/favorites/', include('favorites.urls', namespace='favorites')),

    path('api/auth/token-auth/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token-refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),

    path('api/password-reset/done/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    path('api/password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('api/auth/', include(router_djoser.urls)),  # ← добавили 'api/'

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
