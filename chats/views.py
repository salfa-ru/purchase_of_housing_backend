from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, status, serializers
from rest_framework import permissions
from rest_framework.response import Response

from chats.paginations import ChatPagination
from chats.serializers import (ChatSerializer,
                               MessagesListPASerializer,
                               IdSerializer,
                               MessagesListRealtySerializer,
                               CreateChatRequestSerializer,
                               CreateChatResponseSerializer,
                               IdsListSerializer,
                               BlockingSerializer, )
from chats.services import (get_chats,
                            get_chat_by_id,
                            get_realty_by_id,
                            multiple_delete_chats,
                            get_chats_by_ids,
                            create_blocking, )


@extend_schema(summary='Получение списка переписок')
class ChatListAPIView(generics.ListAPIView):
    """Получение списка переписок пользователя."""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        return get_chats(self.request.user)


@extend_schema(
    summary='Получение списка сообщений в ЛК',
    request=IdSerializer,
    responses={200: MessagesListPASerializer},
)
class MessagesListPAAPIView(generics.CreateAPIView):
    """Получение списка сообщений в переписке (ЛК)."""
    serializer_class = MessagesListPASerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset = get_chat_by_id(
            user=self.request.user,
            data=self.request.data
        )

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


@extend_schema(
    summary='Получение списка сообщений в объявлении',
    request=IdSerializer,
    responses={200: MessagesListRealtySerializer},
)
class MessagesListRealtyAPIView(generics.CreateAPIView):
    """Получение списка сообщений при запросе из объявления."""
    serializer_class = MessagesListRealtySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset = get_realty_by_id(
            data=self.request.data
        )

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


@extend_schema(
    summary='Создание сообщения (из ЛК)',
    request=CreateChatRequestSerializer,
)
class ChatPACreateAPIView(generics.CreateAPIView):
    """Создание сообщения из цепочки сообщений в личном кабинете.
    В id_from передается id переписки (или любого сообщения из цепочки)"""
    serializer_class = CreateChatResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        chat = get_chat_by_id(
            user=self.request.user,
            data=self.request.data
        )
        user_to = chat.user_from if chat.user_from != self.request.user else chat.user_to

        self.request.data.update({
            'user_from': self.request.user.pk,
            'user_to': user_to.pk,
            'realty': chat.realty.pk,
        })
        return super().post(request, *args, **kwargs)


@extend_schema(
    summary='Создание сообщения (из объявления)',
    request=CreateChatRequestSerializer,
)
class ChatRealtyCreateAPIView(generics.CreateAPIView):
    """Создание сообщения из цепочки сообщений в объявления.
    В id_from передается id объявления, по которому идет переписка"""
    serializer_class = CreateChatResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        realty = get_realty_by_id(
            data=self.request.data
        )
        self.request.data.update({
            'user_from': self.request.user.pk,
            'user_to': realty.owner.pk,
            'realty': realty.pk,
        })
        return super().post(request, *args, **kwargs)


@extend_schema(
    request=IdsListSerializer,
    summary='Множественное удаление сообщений',
    responses={200: inline_serializer(
        name='NotificationDestroy',
        fields={
            'detail': serializers.CharField(),
        }
    )},
)
class ChatsDestroyAPIView(generics.CreateAPIView):
    """Множественное удаление сообщений.
    На вход нужно подать список id-шников переписок.
    Удаляются все существующие сообщения, входящие в переписки."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset, ids = get_chats_by_ids(
            current_user=self.request.user,
            data=self.request.data
        )
        multiple_delete_chats(
            current_user=self.request.user,
            chats=queryset
        )

        msg = f'{ids} chats deleted'
        return Response({'detail': msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=IdsListSerializer,
    summary='Блокировка переписок',
    responses=BlockingSerializer(many=True)
)
class ChatsBlockingCreateAPIView(generics.CreateAPIView):
    """В теле запроса передается список id.
    Блокируются собеседники из переписок с указанными id."""
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = BlockingSerializer

    def post(self, request, *args, **kwargs):
        queryset, _ = get_chats_by_ids(
            current_user=self.request.user,
            data=self.request.data
        )
        blocking_list = create_blocking(
            current_user=self.request.user,
            chats=queryset
        )

        serializer = self.get_serializer(blocking_list, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
