from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework import permissions

from users.models import User
from users.permissions import IsAdminOrOwner
from users.serializers import (
    UserFullSerializer,
    UserSelfProfileSerializer,
    UserESAProfileSerializer,
    UserPersonalAccountSerializer,
    UserNewMsgsSerializer
)


@extend_schema_view(
    create=extend_schema(
        summary='Создание "своего" пользователя',
    ),
    list=extend_schema(
        summary='Просмотр списка пользователей (доступен только админу)',
    ),
)
class UserDevViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Создания юзера, просмотра списка пользователей.
    Только для разработки, на прод будет работа через ЕСА"""

    queryset = User.objects.all()
    serializer_class = UserFullSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action == 'destroy':
            return [IsAdminOrOwner()]
        return [permissions.IsAdminUser()]


@extend_schema_view(
    put=extend_schema(
        request=UserSelfProfileSerializer, responses=UserSelfProfileSerializer,
        summary='Изменение профиля пользователя',
    ),
    patch=extend_schema(
        request=UserSelfProfileSerializer, responses=UserSelfProfileSerializer,
        summary='Частичное изменение профиля пользователя',
    ),
    get=extend_schema(
        responses=UserSelfProfileSerializer,
        summary='Просмотр профиля пользователя',
    ),
)
class UserProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Получение/обновление профиля пользователя.
    Для 'своих' пользователей обновление всех полей.
    Для пользователей ЕСА обновление только аватарки."""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if not self.request.user.uuid_esa:
            return UserSelfProfileSerializer
        return UserESAProfileSerializer


@extend_schema_view(
    get=extend_schema(
        summary='Просмотр краткой информации пользователя (в ЛК)',
    ),
)
class UserPersonalAccountRetrieveAPIView(generics.RetrieveAPIView):
    """Получение краткой информации по пользователю.
    Используется в ЛК пользователя."""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPersonalAccountSerializer

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary='Наличие новых сообщений или уведомлений',
    ),
)
class UserNewMsgsRetrieveAPIView(generics.RetrieveAPIView):
    """Получение информации о наличии новых сообщений или уведомлений.
    Используется в шапке."""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserNewMsgsSerializer

    def get_object(self):
        return self.request.user
