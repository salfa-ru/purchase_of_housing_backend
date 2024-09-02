from django.urls import path
from rest_framework import routers

from config.settings import DEBUG
from users.apps import UsersConfig
from users.views import (
    UserDevViewSet,
    UserProfileRetrieveUpdateAPIView,
    UserPersonalAccountRetrieveAPIView,
    UserNewMsgsRetrieveAPIView,
)

app_name = UsersConfig.name

# Роутер для разработки: list, create, delete для User
router_dev = routers.DefaultRouter()
router_dev.register(r'dev', UserDevViewSet, basename='dev')

urlpatterns = [
    path('profile/', UserProfileRetrieveUpdateAPIView.as_view(), name='profile'),
    path('personal-account/', UserPersonalAccountRetrieveAPIView.as_view(), name='personal-account'),
    path('new-msgs/', UserNewMsgsRetrieveAPIView.as_view(), name='new-msgs'),
]

# Пути для разработки: list, create, delete для User
if DEBUG:
    urlpatterns += router_dev.urls
