from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularSwaggerView, SpectacularRedocView, SpectacularAPIView
)
# from rest_framework.authtoken import views

#from users.views import CustomAuthToken
from users.views import (
    CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView
)
from .settings import DEBUG


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/realty/', include('realty.urls')),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/questions/', include('questions.urls', namespace='questions')),
    path('api/notifications/', include('notifications.urls', namespace='notifications')),
    path('api/chats/', include('chats.urls', namespace='chats')),
    path('api/realty-addresses/', include('realty_addresses.urls', namespace='realty-addresses')),
    path('api/complaints/', include('complaints.urls', namespace='complaints')),
    path('api/favorites/', include('favorites.urls', namespace='favorites')),
    path(
        'api/auth/token-auth/',
        CookieTokenObtainPairView.as_view(),
        name='token_obtain_pair'
        ),
    path(
        'api/auth/token-refresh/',
        CookieTokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    # path('api/auth/', include('djoser.urls')),          # эндпоинты для пользователей

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('hidden-health/', lambda request: HttpResponse(status=200)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#if DEBUG:
#    urlpatterns += [
        # path('token-auth/', views.obtain_auth_token)
        #path('token-auth/', CustomAuthToken.as_view(), name='api_token_auth'),  # Use the custom view
#    ]

# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
#     )
