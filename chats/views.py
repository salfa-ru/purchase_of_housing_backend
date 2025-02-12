from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, status, serializers
from rest_framework import permissions
from rest_framework.response import Response
from chats import models as zhats_models
from rest_framework.views import APIView
from chats.paginations import ZhatPagination
from chats.serializers import (
    # ZhatSerializer, NOT NEEDED ANYMORE?
    ChatMessagesSerializer,  # Changed
    MassagesListPASerializer,  # Keep this, but it's less central now
    IdSerializer,
    MassagesListRealtySerializer,
    CreateZhatRequestSerializer,
    CreateZhatResponseSerializer,
    IdsListSerializer,
    BlockingSerializer, UnblockingSerializer,
)
from chats.services import (
    # get_zhats,        # not needed anymore
    # get_zhat_by_id,   # not needed anymore
    get_chats,          # new
    get_chat_by_id,     # new
    get_realty_by_id,
    multiple_delete_zhats,
    get_zhats_by_ids,
    create_blocking, remove_blocking,
    create_message,     # new
)

# TODO - Кажется можно удалять
# @extend_schema(summary='Получение списка ВСЕХ переписок. Только заблокированные - через эндпойнт /blacklist')
# class ZhatListAPIView(generics.ListAPIView):
#     """Получение списка переписок пользователя."""
#     serializer_class = ZhatSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     pagination_class = ZhatPagination
#
#     def get_queryset(self):
#         zhats = get_zhats(self.request.user)
#         is_blacklist = self.kwargs.get("blacklist", False)
#
#         if is_blacklist:
#             filtered_zhats = []
#
#             for zhat in zhats:
#                 if zhats_models.Blocking.objects.filter(user_who=self.request.user,
#                                                         user_whom=zhat.user_to):
#                     filtered_zhats.append(zhat)
#             return filtered_zhats
#
#         else:
#             return zhats


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
                if zhats_models.Blocking.objects.filter(user_who=self.request.user,
                                                        user_whom=other_user):
                    filtered_chats.append(chat)
            return filtered_chats
        else:
            return chats


# TODO - Кажется можно удалять
# @extend_schema(
#     summary='Получение списка сообщений в ЛК',
#     request=IdSerializer,
#     responses={200: MassagesListPASerializer},
# )
# class MassagesListPAAPIView(generics.CreateAPIView):
#     """Получение списка сообщений в переписке (ЛК)."""
#     serializer_class = MassagesListPASerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         queryset = get_zhat_by_id(
#             user=self.request.user,
#             data=self.request.data
#         )
#
#         serializer = self.get_serializer(queryset)
#         return Response(serializer.data)
#


@extend_schema(
    summary='Получение списка сообщений в чате',
    request=IdSerializer, # Keep this for the `chat_id`
    responses={200: ChatMessagesSerializer},  # Now uses the main chat serializer
)
class ChatMessagesAPIView(generics.CreateAPIView): # Renamed
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



# TODO - Кажется можно удалять
# @extend_schema(
#     summary='Создание сообщения (из ЛК)',
#     request=CreateZhatRequestSerializer,
# )
# class ZhatPACreateAPIView(generics.CreateAPIView):
#     """Создание сообщения из цепочки сообщений в личном кабинете.
#     В id_from передается id переписки (или любого сообщения из цепочки)"""
#     serializer_class = CreateZhatResponseSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         zhat = get_zhat_by_id(
#             user=self.request.user,
#             data=self.request.data
#         )
#         user_to = zhat.user_from if zhat.user_from != self.request.user else zhat.user_to
#
#         self.request.data.update({
#             'user_from': self.request.user.pk,
#             'user_to': user_to.pk,
#             'realty': zhat.realty.pk,
#         })
#         return super().post(request, *args, **kwargs)

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


# TODO - Кажется можно удалять
# @extend_schema(
#     summary='Создание сообщения (из объявления)',
#     request=CreateZhatRequestSerializer,
# )
# class ZhatRealtyCreateAPIView(generics.CreateAPIView):
#     """Создание сообщения из цепочки сообщений в объявления.
#     В id_from передается id объявления, по которому идет переписка"""
#     serializer_class = CreateZhatResponseSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         realty = get_realty_by_id(
#             data=self.request.data
#         )
#         self.request.data.update({
#             'user_from': self.request.user.pk,
#             'user_to': realty.owner.pk,
#             'realty': realty.pk,
#         })
#         return super().post(request, *args, **kwargs)

# TODO - Дублированные фукнции какие-то! Создавать надо из одного пойнта - хоть по realty_id хоть по chat_id !!!
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




# В целом не менялось.
@extend_schema(
    request=IdsListSerializer,
    summary='Множественное удаление сообщений',
    responses={200: inline_serializer(
        name='MassageExNotificationDelete',
        fields={
            'detail': serializers.CharField(),
        }
    )},
)
class ZhatsDestroyAPIView(generics.CreateAPIView):
    """Множественное удаление сообщений.
    На вход нужно подать список id-шников переписок.
    Удаляются все существующие сообщения, входящие в переписки."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        queryset, ids = get_zhats_by_ids(
            current_user=self.request.user,
            data=self.request.data
        )
        multiple_delete_zhats(
            current_user=self.request.user,
            zhats=queryset
        )

        msg = f'Сообщения {ids} удалены'
        return Response({'detail': msg}, status=status.HTTP_200_OK)


@extend_schema(
    request=IdsListSerializer,
    summary='Блокировка переписок',
    responses=BlockingSerializer(many=True)
)
class ZhatsBlockingCreateAPIView(generics.CreateAPIView):
    """В теле запроса передается список id.
    Блокируются собеседники из переписок с указанными id."""
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = BlockingSerializer

    def post(self, request, *args, **kwargs):
        queryset, _ = get_zhats_by_ids(
            current_user=self.request.user,
            data=self.request.data
        )
        blocking_list = create_blocking(
            current_user=self.request.user,
            zhats=queryset
        )

        serializer = self.get_serializer(blocking_list, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Разблокировка 4ата',
    request=IdsListSerializer,
    responses={200: MassagesListPASerializer},  # You might want a simpler response here
)
class ZhatRemoveBlocking(APIView):
    queryset = zhats_models.Blocking
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = UnblockingSerializer

    def post(self, request, *args, **kwargs):
        queryset, _ = get_zhats_by_ids(
            current_user=self.request.user,
            data=self.request.data
        )
        remove_blocking(
            current_user=self.request.user,
            zhats=queryset
        )

        return Response({"detail": 'Чаты успешно разблокированы.'})
