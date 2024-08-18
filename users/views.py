from rest_framework import viewsets, mixins
from rest_framework import status
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer


class UserDevViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Вьюсет юзера только для разработки, на прод будет работа через ЕСА"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
