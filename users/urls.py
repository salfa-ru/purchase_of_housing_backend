from django.urls import path
from rest_framework import routers

from config.settings import DEBUG
from users.apps import UsersConfig
from users.views import UserDevViewSet, UserRetrieveUpdateAPIView

app_name = UsersConfig.name

# Роутер для разработки: list, create, delete для User
router_dev = routers.DefaultRouter()
router_dev.register(r'dev', UserDevViewSet, basename='dev')

urlpatterns = [
    path('profile/', UserRetrieveUpdateAPIView.as_view(), name='profile')
]

# Пути для разработки: list, create, delete для User
if DEBUG:
    urlpatterns += router_dev.urls
