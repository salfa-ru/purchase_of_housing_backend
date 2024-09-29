from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework import permissions

from chats.paginations import ChatPagination
from chats.serializers import ChatSerializer
from chats.services import get_chats


@extend_schema(summary='Получение списка переписок пользователя')
class ChatListAPIView(generics.ListAPIView):
    """Получение списка переписок пользователя."""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        return get_chats(self.request.user)


