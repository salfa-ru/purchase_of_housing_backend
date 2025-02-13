from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, status, serializers
from rest_framework import permissions
from rest_framework.response import Response

from rest_framework.views import APIView


from chats.models import Chat, Blocking, Message
from chats.paginations import ZhatPagination
from chats.serializers import (
    ChatMessagesSerializer, CreateMessageResponseSerializer, IdsListSerializer,
    BlockingSerializer, UnblockingSerializer, ChatIdSerializer, CreateMessageRequestSerializer, RealtyIdSerializer,
)
from chats.services import (
    create_message, get_chats_by_ids, get_chat_by_chat_id, get_realty_by_realty_id, get_chats_sorted,
)


@extend_schema(summary='Получение списка чатов пользователя. Только заблокированные - через эндпойнт /blacklist')
class ChatListAPIView(generics.ListAPIView):
    """Получение списка чатов пользователя.
    Самые свежие Чаты идут первыми."""
    serializer_class = ChatMessagesSerializer  # <----- Use the same serializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ZhatPagination

    def get_queryset(self):
        user = self.request.user
        # chats = get_chats(user)
        chats = get_chats_sorted(user)

        is_blacklist = self.kwargs.get("blacklist", False)

        if is_blacklist:
            filtered_chats = []
            for chat in chats:
                other_user = chat.owner if chat.client == user else chat.client
                if Blocking.objects.filter(user_who=user, user_whom=other_user):
                    # Check for visible messages before adding  <----- Added this check
                    if chat.messages.filter(
                            Q(user_from=user, is_deleted_from=False) |
                            Q(user_to=user, is_deleted_to=False)
                    ).exists():
                        filtered_chats.append(chat)


        else:
            filtered_chats = []
            for chat in chats:
                if chat.messages.filter(
                        Q(user_from=user, is_deleted_from=False) |
                        Q(user_to=user, is_deleted_to=False)
                ).exists():
                    filtered_chats.append(chat)
        return filtered_chats

    def list(self, request, *args, **kwargs):  # <----- Added this method
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatMessagesBaseAPIView(generics.CreateAPIView):  # <----- Базовый класс
    """Базовый класс для получения сообщений чата."""
    serializer_class = ChatMessagesSerializer  # <----- Используем ChatMessagesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_chat(self):
        """Получение чата в зависимости от переданных параметров (chat_id или realty_id)."""
        # Этот метод должен быть переопределен в дочерних классах
        raise NotImplementedError("Метод get_chat должен быть переопределен.")

    def post(self, request, *args, **kwargs):
        """Получение и возврат данных чата."""
        chat = self.get_chat()

        # Проверка наличия неудаленных сообщений
        if not chat.messages.filter(
                Q(user_from=request.user, is_deleted_from=False) |
                Q(user_to=request.user, is_deleted_to=False)
        ).exists():
            return Response({"detail": "Чат пуст"}, status=status.HTTP_404_NOT_FOUND)  # <----- Возвращаем 404, если чат пуст

        serializer = self.get_serializer(chat)
        return Response(serializer.data)


@extend_schema(
    summary='Получение списка сообщений в чате',
    request=ChatIdSerializer,
    responses={200: ChatMessagesSerializer},
)
class ChatMessagesAPIView(ChatMessagesBaseAPIView):  # <----- Наследуемся от ChatMessagesBaseAPIView
    """Получение списка сообщений в чате по chat_id"""

    def get_chat(self):
        """Получение чата по chat_id."""
        return get_chat_by_chat_id(
            user=self.request.user,
            chat_id=self.request.data.get('chat_id')
        )


@extend_schema(
    summary='Создание сообщения',
    request=CreateMessageRequestSerializer,
    responses={201: CreateMessageResponseSerializer},
)
class MessageCreateAPIView(generics.CreateAPIView):
    """Универсальный эндпоинт создания сообщения.
    Принимает либо chat_id (для существующего чата),
    либо realty_id (для создания нового чата)"""
    serializer_class = CreateMessageResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = create_message(
            user_from=self.request.user,
            message_text=serializer.validated_data['message'],
            chat_id=serializer.validated_data.get('chat_id'),
            realty_id=serializer.validated_data.get('realty_id')
        )

        response_serializer = self.get_serializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Получение чата по объявлению',
    request=RealtyIdSerializer,
    responses={200: ChatMessagesSerializer},  # <----- Используем ChatMessagesSerializer
)
class RealtyMessagesAPIView(ChatMessagesBaseAPIView):  # <----- Наследуемся от ChatMessagesBaseAPIView
    """Получение чата по realty_id"""
    # serializer_class = RealtyMessagesSerializer   <-----  Удалено. Используем ChatMessagesSerializer

    def get_chat(self):
        """Получение или создание чата по realty_id."""
        realty = get_realty_by_realty_id(
            realty_id=self.request.data.get('realty_id')
        )
        # Получаем или создаем чат
        chat, created = Chat.objects.get_or_create(
            realty=realty,
            owner=realty.owner,
            client=self.request.user
        )
        return chat



@extend_schema(
    request=IdsListSerializer,
    summary='Множественное удаление сообщений по ID чатов',
    responses={200: inline_serializer(
        name='MassageExNotificationDelete',
        fields={
            'detail': serializers.CharField(),
        }
    )},
)
class ZhatsDestroyAPIView(generics.CreateAPIView):
    """Множественное удаление сообщений.
    На вход нужно подать список chat_id.
    Удаляются все существующие сообщения, входящие в эти чаты."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = IdsListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chat_ids = serializer.validated_data['chat_ids']

        chats = get_chats_by_ids(
            current_user=request.user,
            data=request.data
        )

        # TODO - Эффективнее способ
        Message.objects.filter(chat__in=chats, user_from=request.user).update(is_deleted_from=True)
        Message.objects.filter(chat__in=chats, user_to=request.user).update(is_deleted_to=True)

        msg = f'Сообщения в чатах {chat_ids} удалены'
        return Response({'detail': msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=IdsListSerializer,
    summary='Блокировка пользователей по ID чатов',
    responses=BlockingSerializer(many=True),
)
class ZhatsBlockingCreateAPIView(generics.CreateAPIView):
    """В теле запроса передается список chat_id.
    Блокируются собеседники из переписок с указанными id."""
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = BlockingSerializer

    def post(self, request, *args, **kwargs):
        # Получаем только чаты, к которым пользователь имеет доступ
        chats = get_chats_by_ids(
            current_user=request.user,
            data=request.data
        )

        blocking_list = []
        for chat in chats:
            current_user = request.user
            other_user = chat.owner if chat.client == current_user else chat.client

            blocking, created = Blocking.objects.get_or_create(
                user_who=current_user,
                user_whom=other_user
            )
            if created:  # Only add to the list if it was newly created.
                blocking_list.append(blocking)

        serializer = self.get_serializer(blocking_list, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Разблокировка чата',
    request=UnblockingSerializer,
    responses={200:  {"detail": 'Чаты успешно разблокированы.'}},
)
class ZhatRemoveBlocking(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = UnblockingSerializer

    def post(self, request, *args, **kwargs):
        # Получаем только чаты, к которым пользователь имеет доступ
        chats = get_chats_by_ids(
            current_user=request.user,
            data=request.data
        )

        unblock_count = 0
        for chat in chats:
            current_user = request.user
            other_user = chat.owner if chat.client == current_user else chat.client

            deleted_count, _ = Blocking.objects.filter(
                user_who=current_user,
                user_whom=other_user
            ).delete()
            unblock_count += deleted_count

        if unblock_count > 0:
            return Response({"detail": f'Чаты успешно разблокированы.'})
        else:
            return Response(
                {"detail": f'Выбранные чаты не были заблокированы.'},
                status=status.HTTP_400_BAD_REQUEST
            )