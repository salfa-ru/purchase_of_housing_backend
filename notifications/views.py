from typing import List

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import mixins, viewsets, generics, status, serializers, exceptions
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification
from notifications.serializers import NotificationSerializer, IdsListSerializer
from notifications.utils import get_queryset_by_ids


@extend_schema(summary='Получение списка уведомлений пользователя')
class NotificationListAPIView(generics.ListAPIView):
    """Получение списка уведомлений пользователя."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        return Notification.objects.filter(user_to=self.request.user).all()


@extend_schema(
    request=IdsListSerializer,
)
class NotificationUpdateAPIView(generics.UpdateAPIView):
    """Смена статуса уведомлений is_new=False."""
    permission_classes = [IsAuthenticated, ]
    http_method_names = ["patch"]
    serializer_class = NotificationSerializer

    def update(self, request, *args, **kwargs):
        queryset = get_queryset_by_ids(user=self.request.user, data=self.request.data)
        for obj in queryset:
            obj.is_new = False
            obj.save()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# @extend_schema(
#     request=IdsListSerializer(many=True),
#     summary='Удаление'
# )
@extend_schema(
    request=IdsListSerializer(many=True),
    summary='Удаление'
)
class NotificationDestroyAPIView(generics.DestroyAPIView):
    """Удаление."""
    permission_classes = [IsAuthenticated, ]
    # serializer_class = IdsListSerializer


    def destroy(self, request, *args, **kwargs):
        queryset = get_queryset_by_ids(user=self.request.user, data=self.request.data)
        for obj in queryset:
            obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
