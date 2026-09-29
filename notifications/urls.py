from django.urls import path

from notifications.apps import NotificationsConfig
from notifications.views import (
    DeviceTokenCreateAPIView,
    DeviceTokenDeleteAPIView,
    NotificationDeleteAPIView,
    NotificationListAPIView,
    NotificationUpdateAPIView,
)

app_name = NotificationsConfig.name

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='list'),
    path('multiple-del/', NotificationDeleteAPIView.as_view(), name='delete'),
    path('not-new/', NotificationUpdateAPIView.as_view(), name='update'),
    path('devices/', DeviceTokenCreateAPIView.as_view(), name='device-create'),
    path(
        'devices/<str:token>/',
        DeviceTokenDeleteAPIView.as_view(),
        name='device-delete',
    ),
]
