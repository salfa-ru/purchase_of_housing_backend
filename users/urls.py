from django.urls import path
from rest_framework import routers

from config.settings import DEBUG
from users.apps import UsersConfig
from users.views import (
    ChangePhoneAPIView,
    UserDevViewSet,
    UserNewMsgsRetrieveAPIView,
    UserPersonalAccountRetrieveAPIView,
    UserProfileRetrieveUpdateAPIView,
    UserSoftDeleteAPIView,
)

app_name = UsersConfig.name

# ========== РОУТЕР ДЛЯ РАЗРАБОТКИ ==========
# Доступен только при DEBUG=True
router_dev = routers.DefaultRouter()
router_dev.register(r'dev', UserDevViewSet, basename='dev')

# ========== ОСНОВНЫЕ ЭНДПОИНТЫ ==========
urlpatterns = [
    # Профиль пользователя
    path('profile/', UserProfileRetrieveUpdateAPIView.as_view(), name='profile'),
    # Личный кабинет (краткая информация)
    path(
        'personal-account/',
        UserPersonalAccountRetrieveAPIView.as_view(),
        name='personal-account',
    ),
    # Наличие новых сообщений/уведомлений
    path('new-msgs/', UserNewMsgsRetrieveAPIView.as_view(), name='new-msgs'),
    # Смена номера телефона
    path('change-phone/', ChangePhoneAPIView.as_view(), name='change-phone'),
    # Удаление пользователя (только для администратора или владельца)
    path('dev/delete/<int:id>', UserSoftDeleteAPIView.as_view(), name='destroy'),
]

# ========== ПУТИ ДЛЯ РАЗРАБОТКИ ==========
if DEBUG:
    urlpatterns += router_dev.urls
