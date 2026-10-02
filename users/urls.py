from django.urls import path
from rest_framework import routers

from config.settings import DEBUG
from users.apps import UsersConfig
from users.views import (
    ChangePhoneAPIView,
    UserAvatarAPIView,
    UserDevViewSet,
    UserNewMsgsRetrieveAPIView,
    UserPersonalAccountRetrieveAPIView,
    UserProfileRetrieveUpdateAPIView,
    UserSoftDeleteAPIView,
)

app_name = UsersConfig.name

# ========== РОУТЕР ДЛЯ РАЗРАБОТКИ ==========
router_dev = routers.DefaultRouter()
router_dev.register(r'dev', UserDevViewSet, basename='dev')

# ========== ОСНОВНЫЕ ЭНДПОИНТЫ ==========
urlpatterns = [
    path('profile/', UserProfileRetrieveUpdateAPIView.as_view(), name='profile'),
    path('me/avatar/', UserAvatarAPIView.as_view(), name='avatar'),
    path(
        'personal-account/',
        UserPersonalAccountRetrieveAPIView.as_view(),
        name='personal-account',
    ),
    path('new-msgs/', UserNewMsgsRetrieveAPIView.as_view(), name='new-msgs'),
    path('change-phone/', ChangePhoneAPIView.as_view(), name='change-phone'),
    path('dev/delete/<int:id>', UserSoftDeleteAPIView.as_view(), name='destroy'),
]

# ========== ПУТИ ДЛЯ РАЗРАБОТКИ ==========
if DEBUG:
    urlpatterns += router_dev.urls
