from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification
from notifications.paginations import NotificationPagination
from notifications.serializers import IdsNotifListSerializer, NotificationSerializer
from notifications.utils import get_queryset_by_ids


@extend_schema(
    tags=['Уведомления'], summary='Получение списка уведомлений пользователя'
)
class NotificationListAPIView(generics.ListAPIView):
    """Получение списка уведомлений пользователя."""

    serializer_class = NotificationSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = NotificationPagination

    def get_queryset(self):
        return Notification.objects.filter(user_to=self.request.user).all()

    # Переопределяем метод list ДЛЯ ПОЛУЧЕНИЯ UNREAD TOTAL
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        # Считаем общее количество непрочитанных сообщений
        unread_total = Notification.objects.filter(
            user_to=request.user,
            is_new=True,
        ).count()

        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request}
            )
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
    tags=['Уведомления'],
    request=IdsNotifListSerializer,
    summary='Смена статуса уведомлений на "прочитано"',
)
class NotificationUpdateAPIView(generics.UpdateAPIView):
    """Смена статуса уведомлений is_new=False.
    На вход нужно подать список id-шников."""

    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ['patch']
    serializer_class = NotificationSerializer

    def update(self, request, *args, **kwargs):
        queryset, _ = get_queryset_by_ids(
            user=self.request.user, data=self.request.data
        )
        for obj in queryset:
            obj.is_new = False
            obj.save()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['Уведомления'],
    request=IdsNotifListSerializer,
    summary='Множественное удаление уведомлений',
    responses={
        200: inline_serializer(
            name='NotificationDelete',
            fields={
                'detail': serializers.CharField(),
            },
        )
    },
)
class NotificationDeleteAPIView(generics.CreateAPIView):
    """Множественное удаление уведомлений.
    На вход нужно подать список id-шников."""

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        queryset, ids = get_queryset_by_ids(
            user=self.request.user, data=self.request.data
        )
        for obj in queryset:
            obj.delete()

        msg = f'{ids} notifications deleted'
        return Response({'detail': msg}, status=status.HTTP_200_OK)
