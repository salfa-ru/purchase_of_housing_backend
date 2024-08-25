from django.urls import path
from rest_framework import routers

from config.settings import DEBUG
from users.apps import UsersConfig
from users.views import UserDevViewSet, UserRetrieveUpdateAPIView

app_name = UsersConfig.name

# Роутер для разработки: list, create, delete для User
router_dev = routers.DefaultRouter()
router_dev.register(r'users-dev', UserDevViewSet, basename='users')

urlpatterns = [
    path('users/', UserRetrieveUpdateAPIView.as_view(), name='users')
]

# Пути для разработки: list, create, delete для User
if DEBUG:
    urlpatterns += router_dev.urls
