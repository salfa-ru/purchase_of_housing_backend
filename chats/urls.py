from django.urls import path

from chats.apps import ChatsConfig
from chats.views import (
    ZhatListAPIView,
    MassagesListPAAPIView,
    MassagesListRealtyAPIView,
    ZhatPACreateAPIView,
    ZhatRealtyCreateAPIView,
    ZhatsDestroyAPIView,
    ZhatsBlockingCreateAPIView, ZhatRemoveBlocking,
)

app_name = ChatsConfig.name

urlpatterns = [
    path('', ZhatListAPIView.as_view(), name='list'),
    path('blacklist/', ZhatListAPIView.as_view(), {"blacklist": True}, name='zhat-blacklist'),
    path('talk/', MassagesListPAAPIView.as_view(), name='msg-list-pa'),
    path('realty/msgs/', MassagesListRealtyAPIView.as_view(), name='msg-list-realty'),
    path('new/pa/', ZhatPACreateAPIView.as_view(), name='create-pa'),
    path('new/realty/', ZhatRealtyCreateAPIView.as_view(), name='create-realty'),
    path('multiple-del/', ZhatsDestroyAPIView.as_view(), name='destroy'),
    path('block/', ZhatsBlockingCreateAPIView.as_view(), name='blocking'),
    path('unblock/', ZhatRemoveBlocking.as_view(), name='unblocking'),
]
