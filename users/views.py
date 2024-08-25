from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework import permissions
from rest_framework import parsers

from users.models import User
from users.permissions import IsAdminOrOwner
from users.serializers import UserDevSerializer, UserSelfSerializer, UserESASerializer


class UserDevViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Вьюсет юзера только для разработки, на прод будет работа через ЕСА"""

    queryset = User.objects.all()
    serializer_class = UserDevSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action == 'destroy':
            return [IsAdminOrOwner()]
        return [permissions.IsAdminUser()]


# Переопределяем схемы для swagger для каждого метода, т.к. переопределили get_serializer_class
@method_decorator(name='put', decorator=swagger_auto_schema(
    responses={200: UserSelfSerializer()}, request_body=UserSelfSerializer,
))
@method_decorator(name='patch', decorator=swagger_auto_schema(
    responses={200: UserSelfSerializer()}, request_body=UserSelfSerializer,
))
@method_decorator(name='get', decorator=swagger_auto_schema(
    responses={200: UserSelfSerializer()},
))
class UserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Вьюсет получение/обновление профиля пользователя.
    Для 'своих' пользователей обновление всех полей.
    Для пользователей ЕСА обновление только аватарки."""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if not self.request.user.uuid_esa:
            return UserSelfSerializer
        return UserESASerializer
