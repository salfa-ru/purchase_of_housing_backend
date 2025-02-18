from django.urls import path

from chats.apps import ChatsConfig
from chats.views import (
    ChatListAPIView,
    MessageCreateAPIView, ChatMessagesAPIView,
    ChatsDeleteAPIView,
    ChatsBlockingCreateAPIView, ChatRemoveBlocking,
)

app_name = ChatsConfig.name

urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list'),
    path('blacklist/', ChatListAPIView.as_view(), {"blacklist": True}, name='chat-blacklist'),

    path('send-message/', MessageCreateAPIView.as_view(), name='create-message'),  # Новый универсальный эндпоинт
    path('show-chat/', ChatMessagesAPIView.as_view(), name='chat-messages'),       # Новый универсальный эндпоинт

    path('delete-chats/', ChatsDeleteAPIView.as_view(), name='delete-chats'),  # ex-multiple-del

    path('block/', ChatsBlockingCreateAPIView.as_view(), name='blocking'),
    path('unblock/', ChatRemoveBlocking.as_view(), name='unblocking'),
]

