from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, status, serializers, permissions, exceptions
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter

from chats.models import Chat, Blocking, Message
from chats.paginations import ConfigurablePagination
from chats.serializers import (
    ChatMessagesSerializer, CreateMessageResponseSerializer, IdsListSerializer,
    BlockingSerializer, UnblockingSerializer, CreateMessageRequestSerializer, MessageSerializer,
)
from chats.services import (
    create_message, get_chats_by_ids, get_chat_by_chat_id,
    get_realty_by_realty_id, get_chats_sorted,
)
from config import constants


# TODO - Внимание! При пагинации сообщений в чате - может быть непрочитанные будут на предыдущей странице!
# I came up with this approach: well, I have paginator there, and so while I am asking for "the last page"
# of messages, I can forcely show not the last one but the page where the "oldest" unread message is!
# (thus I am on let's say page 2 of messages, but when I will scroll down, i will have to download page 1 of messages
# (as the last ones are one the first pages). what do you think?


class ChatsPagination(ConfigurablePagination):
    """Pagination for Chat lists (/chats/ and /chats/blacklist/)."""
    page_size = constants.CHATS_PAGESIZE_DEFAULT
    max_page_size = constants.CHATS_PAGESIZE_MAX
    pagination_config_name = "CHATS"


class MessagesPagination(ConfigurablePagination):
    """Pagination for messages within a chat (/chats/show-chat/)."""
    page_size = constants.MESSAGES_PAGESIZE_DEFAULT
    max_page_size = constants.MESSAGES_PAGESIZE_MAX
    pagination_config_name = "MESSAGES"


@extend_schema(
    summary='Получение списка чатов пользователя. Только заблокированные - через эндпойнт /blacklist',
    parameters=[
        OpenApiParameter(name='page', type=int, location=OpenApiParameter.QUERY, description='Номер страницы'),
        OpenApiParameter(name='page_size', type=int, location=OpenApiParameter.QUERY,
                         description=f'Количество объектов на странице '
                                     f'(по умолчанию {constants.CHATS_PAGESIZE_DEFAULT}, '
                                     f'максимум {constants.CHATS_PAGESIZE_MAX}), '
                                     f'настраивается константами CHATS_PAGESIZE'),
    ],
)
class ChatListAPIView(generics.ListAPIView):
    """Получение списка чатов пользователя.
    Самые свежие Чаты идут первыми."""
    serializer_class = ChatMessagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatsPagination

    def get_queryset(self):
        user = self.request.user
        chats = get_chats_sorted(user)

        is_blacklist = self.kwargs.get("blacklist", False)

        if is_blacklist:
            filtered_chats = []
            for chat in chats:
                other_user = chat.owner if chat.client == user else chat.client
                if Blocking.objects.filter(user_who=user, user_whom=other_user):
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


@extend_schema(
    summary='Получение списка сообщений в чате по chat_id ИЛИ realty_id',
    request=inline_serializer(
        name='ChatOrRealtyId',
        fields={
            'chat_id': serializers.IntegerField(min_value=1, required=False),
            'realty_id': serializers.IntegerField(min_value=1, required=False),
        }
    ),
    parameters=[
        OpenApiParameter(name='page', type=int, location=OpenApiParameter.QUERY, description='Номер страницы'),
        OpenApiParameter(name='page_size', type=int, location=OpenApiParameter.QUERY,
                         description=f'Количество объектов на странице '
                                     f'(по умолчанию {constants.MESSAGES_PAGESIZE_DEFAULT}, '
                                     f'максимум {constants.MESSAGES_PAGESIZE_MAX}), '
                                     f'настраивается константами MESSAGES_PAGESIZE'),
    ],
    responses={200: ChatMessagesSerializer},
)
class ChatMessagesAPIView(generics.CreateAPIView):
    """Получение списка сообщений в чате по chat_id ИЛИ realty_id"""
    serializer_class = ChatMessagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessagesPagination

    def get_chat(self, request):
        chat_id = request.data.get('chat_id')
        realty_id = request.data.get('realty_id')

        if (chat_id is not None and realty_id is not None) or (chat_id is None and realty_id is None):

            # Уродливо показывается - зато как 400 ошибка
            raise exceptions.ValidationError(detail="Нужен либо chat_id либо realty_id, а не оба (или ни одного)")

        if chat_id:
            return get_chat_by_chat_id(user=request.user, chat_id=chat_id)
        elif realty_id:
            realty = get_realty_by_realty_id(realty_id=realty_id)
            chat, created = Chat.objects.get_or_create(
                realty=realty,
                owner=realty.owner,
                client=request.user
            )
            return chat

    def post(self, request, *args, **kwargs):
        try:
            chat = self.get_chat(request)
        except exceptions.ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        messages = chat.messages.filter(
            Q(user_from=request.user, is_deleted_from=False) |
            Q(user_to=request.user, is_deleted_to=False)
        )
        if not messages.exists():
            return Response({"detail": "Чат пуст"}, status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(messages.order_by('-created_at'))
        
        # TODO - ПРОВЕРИТЬ - Установка даты чтения сообщения получателем (место 1 из 2)
        print("ПРОВЕРИТЬ - Установка даты чтения сообщения получателем (место 1 из 2)!")
        if page is not None:
            serializer = ChatMessagesSerializer(instance=chat, context={'request': request})
            paginated_messages = MessageSerializer(page, many=True, context={'request': request}).data
            response_data = serializer.data
            response_data['messages'] = paginated_messages

            # --- MODIFICATION STARTS HERE ---
            unread_messages = messages.filter(user_to=request.user, is_new=True)
            unread_messages.update(is_new=False, read_at=timezone.now())  # Set is_new and read_at
            # --- MODIFICATION ENDS HERE ---
            return self.get_paginated_response(response_data)

        else:
            serializer = ChatMessagesSerializer(instance=chat, context={'request': request})

            # --- MODIFICATION STARTS HERE ---
            unread_messages = messages.filter(user_to=request.user, is_new=True)
            unread_messages.update(is_new=False, read_at=timezone.now())  # Set is_new and read_at
            # --- MODIFICATION ENDS HERE ---

            return Response(serializer.data)


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
    request=IdsListSerializer,
    summary='Множественное удаление сообщений по ID чатов',
    responses={200: inline_serializer(
        name='MessagesInChatsDelete',
        fields={
            'detail': serializers.CharField(),
        }
    )},
)
class ChatsDeleteAPIView(generics.CreateAPIView):
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

        Message.objects.filter(chat__in=chats, user_from=request.user).update(is_deleted_from=True)
        Message.objects.filter(chat__in=chats, user_to=request.user).update(is_deleted_to=True)

        msg = f'Сообщения в чатах {chat_ids} удалены'
        return Response({'detail': msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=IdsListSerializer,
    summary='Блокировка пользователей по ID чатов',
    responses=BlockingSerializer(many=True),
)
class ChatsBlockingCreateAPIView(generics.CreateAPIView):
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
class ChatRemoveBlocking(APIView):
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
