from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, status, serializers
from rest_framework import permissions
from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework import exceptions

from chats.models import Chat, Blocking
from chats.paginations import ZhatPagination
from chats.serializers import (
    ChatMessagesSerializer,  # Changed
    IdSerializer,
    MassagesListRealtySerializer,
    CreateZhatRequestSerializer,
    CreateZhatResponseSerializer,
    IdsListSerializer,
    BlockingSerializer, UnblockingSerializer,
)
from chats.services import (
    get_chats,
    get_chat_by_id,
    get_realty_by_id,
    create_message, get_chats_by_ids,
)


@extend_schema(summary='Получение списка чатов пользователя. Только заблокированные - через эндпойнт /blacklist')
class ChatListAPIView(generics.ListAPIView):  # Renamed
    """Получение списка чатов пользователя."""
    serializer_class = ChatMessagesSerializer  # Changed
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ZhatPagination

    def get_queryset(self):
        chats = get_chats(self.request.user)
        is_blacklist = self.kwargs.get("blacklist", False)

        if is_blacklist:
            filtered_chats = []
            for chat in chats:
                other_user = chat.owner if chat.client == self.request.user else chat.client
                if Blocking.objects.filter(user_who=self.request.user,
                                           user_whom=other_user):
                    filtered_chats.append(chat)
            return filtered_chats
        else:
            return chats


@extend_schema(
    summary='Получение списка сообщений в чате',
    request=IdSerializer,  # Keep this for the `chat_id`
    responses={200: ChatMessagesSerializer},  # Now uses the main chat serializer
)
class ChatMessagesAPIView(generics.CreateAPIView):  # Renamed
    """Получение списка сообщений в чате (ЛК)."""
    serializer_class = ChatMessagesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        chat = get_chat_by_id(
            user=self.request.user,
            data=self.request.data
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data)


""" ЗАЧЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕМ ??????? """
...
...
...


@extend_schema(
    summary='Получение списка сообщений в объявлении',
    request=IdSerializer,
    responses={200: MassagesListRealtySerializer},
)
class MassagesListRealtyAPIView(generics.CreateAPIView):
    """Получение списка сообщений при запросе из объявления."""
    serializer_class = MassagesListRealtySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset = get_realty_by_id(
            data=self.request.data
        )

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


@extend_schema(
    summary='Создание сообщения (из ЛК)',
    request=CreateZhatRequestSerializer,
)
class ChatMessageCreateAPIView(generics.CreateAPIView):  # Renamed
    """Создание сообщения из цепочки сообщений в личном кабинете.
    В id_from передается id чата"""
    serializer_class = CreateZhatResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        chat = get_chat_by_id(
            user=self.request.user,
            data=self.request.data
        )

        message = create_message(
            user_from=self.request.user,
            chat=chat,
            message_text=self.request.data['message']
        )

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# TODO - Дублированные функции какие-то! Создавать надо из одного пойнта - хоть по realty_id хоть по chat_id !!!
@extend_schema(
    summary='Создание сообщения (из объявления)',
    request=CreateZhatRequestSerializer,
)
class ZhatRealtyCreateAPIView(generics.CreateAPIView):
    """Создание сообщения из цепочки сообщений в объявления.
    В id_from передается id объявления, по которому идет переписка"""
    serializer_class = CreateZhatResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        realty = get_realty_by_id(
            data=self.request.data
        )

        message = create_message(
            user_from=self.request.user,
            realty=realty,
            message_text=self.request.data['message']
        )

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=IdsListSerializer,  # We'll reuse this, but it now contains chat_ids.
    summary='Множественное удаление сообщений по ID чатов',  # Updated summary
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
    Удаляются все существующие сообщения, входящие в эти чаты."""  # Corrected docstring
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = IdsListSerializer(data=request.data)  # validate incoming ids
        serializer.is_valid(raise_exception=True)
        chat_ids = serializer.validated_data['ids']  # takes ids of chats

        chats = get_chats_by_ids(  # Reuse our existing function
            current_user=request.user,
            data=request.data  # Pass the request data to validate
        )

        for chat in chats:
            # Mark messages as deleted for the current user.
            if request.user == chat.owner:
                chat.messages.filter(user_from=request.user).update(is_deleted_from=True)
                chat.messages.filter(user_to=request.user).update(is_deleted_to=True)
            else:  # current user is a client
                chat.messages.filter(user_from=request.user).update(is_deleted_from=True)
                chat.messages.filter(user_to=request.user).update(is_deleted_to=True)

        msg = f'Сообщения в чатах {chat_ids} удалены'
        return Response({'detail': msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=IdsListSerializer,  # We'll keep and modify this
    summary='Блокировка пользователей по ID чатов',  # Updated description
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

            if not Blocking.objects.filter(user_who=current_user, user_whom=other_user).exists():
                blocking = Blocking(user_who=current_user, user_whom=other_user)
                blocking_list.append(blocking)

        Blocking.objects.bulk_create(blocking_list)
        serializer = self.get_serializer(blocking_list, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Разблокировка чата',
    request=UnblockingSerializer,
    responses={200:  {"detail": 'Чаты успешно разблокированы.'}},  # You might want a simpler response here
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
