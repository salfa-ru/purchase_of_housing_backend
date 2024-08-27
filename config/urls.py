from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views
from .yasg import urlpatterns as doc_urls

from .settings import DEBUG


urlpatterns = [
    path("admin/", admin.site.urls),
    path("realty/", include("realty.urls")),
    path("", include("users.urls", namespace="users")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if DEBUG:
    urlpatterns += [path("token-auth/", views.obtain_auth_token)]

urlpatterns += doc_urls
