from django.urls import path

from chats.apps import ChatsConfig
from chats.views import ChatListAPIView

app_name = ChatsConfig.name

urlpatterns = [
    path('', ChatListAPIView.as_view(), name='list')
]