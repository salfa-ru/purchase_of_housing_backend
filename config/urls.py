from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularSwaggerView, SpectacularRedocView, SpectacularAPIView
from rest_framework.authtoken import views

from .settings import DEBUG


urlpatterns = [
    path('realty/', include('realty.urls')),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('questions/', include('questions.urls', namespace='questions')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('chats/', include('chats.urls', namespace='chats')),
    path('complaints/', include('complaints.urls', namespace='complaints')),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if DEBUG:
    urlpatterns += [
        path('token-auth/', views.obtain_auth_token)
    ]
