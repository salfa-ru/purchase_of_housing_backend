from django.urls import path
from rest_framework.routers import DefaultRouter

from notifications.apps import NotificationsConfig
from notifications.views import (
    NotificationListAPIView,
    NotificationDestroyAPIView,
    NotificationUpdateAPIView
)

app_name = NotificationsConfig.name

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='list'),
    path('multiple-del/', NotificationDestroyAPIView.as_view(), name='delete'),
    path('not-new/', NotificationUpdateAPIView.as_view(), name='update'),
]
