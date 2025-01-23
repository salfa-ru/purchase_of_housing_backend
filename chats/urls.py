from django.urls import path

from chats.apps import ChatsConfig
from chats.views import (
    ChatListAPIView,
    MessagesListPAAPIView,
    MessagesListRealtyAPIView,
    ChatPACreateAPIView,
    ChatRealtyCreateAPIView,
    ChatsDestroyAPIView,
    ChatsBlockingCreateAPIView, ChatRemoveBlocking,
)

app_name = ChatsConfig.name

urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list'),
    path('talk/', MessagesListPAAPIView.as_view(), name='msg-list-pa'),
    path('realty/msgs/', MessagesListRealtyAPIView.as_view(), name='msg-list-realty'),
    path('new/pa/', ChatPACreateAPIView.as_view(), name='create-pa'),
    path('new/realty/', ChatRealtyCreateAPIView.as_view(), name='create-realty'),
    path('multiple-del/', ChatsDestroyAPIView.as_view(), name='destroy'),
    path('block/', ChatsBlockingCreateAPIView.as_view(), name='blocking'),
    path('unblock/', ChatRemoveBlocking.as_view(), name='unblocking'),
]
