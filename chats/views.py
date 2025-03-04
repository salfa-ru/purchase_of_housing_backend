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
    BlockingSerializer, CreateMessageRequestSerializer, MessageSerializer,
    BlockingRequestSerializer, UserInfoIdNameSerializer, BlockingResponseSerializer, UnblockingRequestSerializer,
)
from chats.services import (
    create_message, get_chats_by_ids, get_chat_by_chat_id,
    get_realty_by_realty_id, get_chats_sorted, get_users_to_block_unblock, get_chats_from_users,
    get_realties_from_users,
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
    ]
)
class ChatListAPIView(generics.ListAPIView):
    """Получение списка чатов пользователя.
    Самые свежие Чаты идут первыми.
    <ul>
    <li><strong>unread_total</strong> - количество непрочитанных сообщений пользователем ВООБЩЕ
    <font color="#ce591b"> - В схеме Swagger его не видно!!</font></li>
    <li><strong>unread </strong>- количество непрочитанных сообщений в каждом чате</li></ul>

    Не смотрите не структуру "образца" JSON, смотрите на реально приходящий JSON! """
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

    def list(self, request, *args, **kwargs):  # Переопределяем метод list ДЛЯ ПОЛУЧЕНИЯ UNREAD TOTAL
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        # Считаем общее количество непрочитанных сообщений
        unread_total = Message.objects.filter(
            user_to=request.user,
            is_new=True,
            is_deleted_to=False
        ).count()


        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            paginated_response = self.get_paginated_response(serializer.data)

            # Создаем новый словарь и добавляем unread_total в начало  # <----------
            new_data = {'unread_total': unread_total}
            new_data.update(paginated_response.data)  # Добавляем остальные данные
            paginated_response.data = new_data  # Заменяем данные
            return paginated_response

        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        response_data.insert(0, {'unread_total': unread_total})
        return Response(response_data)

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
    summary='Отправка сообщения',
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
    responses={
        200: inline_serializer(  # Use inline_serializer for a custom response
            name='MessagesInChatsDeleteResponse',
            fields={
                'deleted_chat_ids': serializers.ListField(child=serializers.IntegerField()),
                'detail': serializers.CharField(),
            }
        ),
        400: inline_serializer(
            name='MessagesInChatsDeleteError',
            fields={
                'not_found_or_empty_chats': serializers.ListField(child=serializers.IntegerField()),
                'found_chats': serializers.ListField(child=serializers.IntegerField()),
                'detail': serializers.CharField(),
            }
        ),
    },
)
class ChatsDeleteAPIView(generics.CreateAPIView):
    """Множественное удаление сообщений.
    На вход нужно подать список chat_id.
    Удаляются все существующие сообщения, входящие в эти чаты.
    Если хотя бы в одном из указанных чатов нет сообщений для удаления,
    удаление не производится, и возвращается ошибка.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = IdsListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_ids = serializer.validated_data['chat_ids']

        # 1. Получаем чаты, доступные пользователю, и проверяем их наличие.
        try:
            chats = get_chats_by_ids(
                current_user=request.user,
                data=request.data
            )
        except exceptions.NotFound as e:  # перехват ошибки, брошенной в get_chats_by_ids
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        found_chat_ids = [chat.chat_id for chat in chats]
        not_found_chat_ids = list(set(chat_ids) - set(found_chat_ids))

        # 2. Проверяем, есть ли в каждом найденном чате сообщения для удаления.
        chats_without_messages = []
        for chat in chats:
            has_messages = Message.objects.filter(
                Q(chat=chat) &
                (Q(user_from=request.user, is_deleted_from=False) |
                 Q(user_to=request.user, is_deleted_to=False))
            ).exists()
            if not has_messages:
                chats_without_messages.append(chat.chat_id)

        # 3. Если есть чаты без сообщений ИЛИ не все чаты найдены, возвращаем ошибку.
        if chats_without_messages or not_found_chat_ids:
            response_data = {
                'not_found_or_empty_chats': not_found_chat_ids + chats_without_messages,
                'found_chats': [chat_id for chat_id in found_chat_ids if chat_id not in chats_without_messages],
                'detail': 'Удаление не произошло.  '
                          'Некоторые чаты не найдены или не содержат сообщений для удаления.'
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # 4. Если все чаты найдены и содержат сообщения, удаляем.
        Message.objects.filter(chat__in=chats, user_from=request.user).update(is_deleted_from=True)
        Message.objects.filter(chat__in=chats, user_to=request.user).update(is_deleted_to=True)

        response_data = {
            'deleted_chat_ids': found_chat_ids,
            'detail': 'Чаты успешно удалены.'
        }
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    request=BlockingRequestSerializer,
    summary='Блокировка переписок',
    responses={201: BlockingResponseSerializer},
)
class ChatsBlockingCreateAPIView(generics.CreateAPIView):
    """Блокировка переписок по chat_ids, user_ids, или realty_ids
    <strong> (только по одному из трех параметров). </strong> Рекомендую в основном пользоваться chat_id.<br>
    Блокировка не дает текущему пользователю написать тому, кого он заблокировал. Себя заблокировать нельзя. """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlockingSerializer  # For creating Blocking instances

    def post(self, request, *args, **kwargs):
        serializer = BlockingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        current_user = request.user
        try:
            users_to_block = get_users_to_block_unblock(
                current_user,
                chat_ids=validated_data.get('chat_ids'),
                user_ids=validated_data.get('user_ids'),
                realty_ids=validated_data.get('realty_ids')
            )
        except exceptions.NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except exceptions.ValidationError as e:  # Catch self-blocking attempt
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create Blocking instances
        blocking_list = []
        for user in users_to_block:
            blocking, created = Blocking.objects.get_or_create(
                user_who=current_user,
                user_whom=user
            )
            blocking_list.append(blocking)  # add any way, created or not

        blocked_chats = get_chats_from_users(current_user, users_to_block)
        blocked_realties = get_realties_from_users(current_user, users_to_block)

        response_data = {
            'current_user_debug': f"#{current_user.id} - {current_user.first_name}",
            "blocked_users": UserInfoIdNameSerializer(users_to_block, many=True).data,
            "blocked_chat_ids": blocked_chats,
            "blocked_realty_ids": blocked_realties
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=UnblockingRequestSerializer,
    summary='Разблокировка переписок',
    responses={200: BlockingResponseSerializer},
)
class ChatRemoveBlocking(APIView):
    """Разблокировка переписок по chat_ids, user_ids, или realty_ids
    <strong> (только по одному из трех параметров). </strong> Рекомендую в основном пользоваться chat_id.<br>
    Разблокировка по realty_id или user_id может быть удобна для написания сообщений по новому объявлению
    пользователя, который заблокирован в других чатах"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UnblockingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        current_user = request.user

        try:
            users_to_unblock = get_users_to_block_unblock(
                current_user,
                chat_ids=validated_data.get('chat_ids'),
                user_ids=validated_data.get('user_ids'),
                realty_ids=validated_data.get('realty_ids')
            )
        except exceptions.NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except exceptions.ValidationError as e:  # Catch self-unblocking attempt
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        unblock_count = 0
        for user in users_to_unblock:
            deleted_count, _ = Blocking.objects.filter(
                user_who=current_user,
                user_whom=user
            ).delete()
            unblock_count += deleted_count

        blocked_chats = get_chats_from_users(current_user, users_to_unblock)
        blocked_realties = get_realties_from_users(current_user, users_to_unblock)

        response_data = {
            'current_user_debug': f"#{current_user.id} - {current_user.username}",
            "unblocked_users": UserInfoIdNameSerializer(users_to_unblock, many=True).data,  # it shows users anyway
            "unblocked_chats": blocked_chats,
            "unblocked_realties": blocked_realties
        }

        if unblock_count > 0:
            return Response(response_data, status=status.HTTP_200_OK)  # response_data
        else:
            return Response(response_data, status=status.HTTP_200_OK)  # it's not an error
