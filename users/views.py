from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework import permissions

from users.models import User
from users.permissions import IsAdminOrOwner
from users.serializers import UserFullSerializer, UserSelfProfileSerializer, UserESAProfileSerializer


class UserDevViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Вьюсет юзера только для разработки, на прод будет работа через ЕСА"""

    queryset = User.objects.all()
    serializer_class = UserFullSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action == 'destroy':
            return [IsAdminOrOwner()]
        return [permissions.IsAdminUser()]


@extend_schema_view(
    put=extend_schema(request=UserSelfProfileSerializer, responses=UserSelfProfileSerializer,),
    patch=extend_schema(request=UserSelfProfileSerializer, responses=UserSelfProfileSerializer,),
    get=extend_schema(responses=UserSelfProfileSerializer,),
)
class UserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Вьюсет получение/обновление профиля пользователя.
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
