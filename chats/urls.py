from django.urls import path

from chats.apps import ChatsConfig
from chats.views import (
    ChatListAPIView,
    ChatMessagesAPIView,
    ZhatsDestroyAPIView,
    ZhatsBlockingCreateAPIView, ZhatRemoveBlocking, RealtyMessagesAPIView, MessageCreateAPIView,
)

app_name = ChatsConfig.name


urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list'),
    path('blacklist/', ChatListAPIView.as_view(), {"blacklist": True}, name='chat-blacklist'),
    path('talk/', ChatMessagesAPIView.as_view(), name='chat-messages'),
    path('realty/msgs/', RealtyMessagesAPIView.as_view(), name='realty-messages'),
    path('new/', MessageCreateAPIView.as_view(), name='create-message'),  # Новый универсальный эндпоинт
    # path('new/pa/', MessageCreateAPIView.as_view(), name='create-pa'),  # Create message in chat
    # path('new/realty/', MessageCreateAPIView.as_view(), name='create-realty'),
    path('multiple-del/', ZhatsDestroyAPIView.as_view(), name='destroy'),
    path('block/', ZhatsBlockingCreateAPIView.as_view(), name='blocking'),
    path('unblock/', ZhatRemoveBlocking.as_view(), name='unblocking'),
]

