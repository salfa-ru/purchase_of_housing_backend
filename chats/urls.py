from django.urls import path

from chats.apps import ChatsConfig
from chats.views import ChatListAPIView, MessagesListAPIView

app_name = ChatsConfig.name

urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list'),
    path('talk/', MessagesListAPIView.as_view(), name='msg-list'),
]