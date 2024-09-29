from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response

from chats.paginations import ChatPagination
from chats.serializers import (ChatSerializer,
                               MessagesListSerializer,
                               IdSerializer)
from chats.services import get_chats, get_chat_by_id


@extend_schema(summary='Получение списка переписок')
class ChatListAPIView(generics.ListAPIView):
    """Получение списка переписок пользователя."""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        return get_chats(self.request.user)


@extend_schema(
    summary='Получение списка сообщений',
    request=IdSerializer,
    responses={200: MessagesListSerializer},

)
class MessagesListAPIView(generics.CreateAPIView):
    """Получение списка сообщений в переписке."""
    serializer_class = MessagesListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset = get_chat_by_id(
            user=self.request.user,
            data=self.request.data
        )

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
