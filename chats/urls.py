from django.urls import path

from chats.apps import ChatsConfig
from chats.views import (
    ChatListAPIView,  # Changed
    ChatMessagesAPIView,  # Changed
    MassagesListRealtyAPIView,
    ChatMessageCreateAPIView,  # Changed
    ZhatRealtyCreateAPIView,
    ZhatsDestroyAPIView,
    ZhatsBlockingCreateAPIView, ZhatRemoveBlocking,
)

app_name = ChatsConfig.name

urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list'),  # Now lists chats
    path('blacklist/', ChatListAPIView.as_view(), {"blacklist": True}, name='chat-blacklist'),  # corrected
    path('talk/', ChatMessagesAPIView.as_view(), name='msg-list-pa'),  # Now for a specific chat
    path('realty/msgs/', MassagesListRealtyAPIView.as_view(), name='msg-list-realty'),
    path('new/pa/', ChatMessageCreateAPIView.as_view(), name='create-pa'),  # Create message in chat
    path('new/realty/', ZhatRealtyCreateAPIView.as_view(), name='create-realty'),
    path('multiple-del/', ZhatsDestroyAPIView.as_view(), name='destroy'),
    path('block/', ZhatsBlockingCreateAPIView.as_view(), name='blocking'),
    path('unblock/', ZhatRemoveBlocking.as_view(), name='unblocking'),
]
