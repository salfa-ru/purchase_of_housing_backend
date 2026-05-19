from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import (
    generics,
    mixins,
    permissions,
    status,  # <---xxx--- удаление пользователя
    viewsets,
)
from rest_framework.exceptions import (  # <---xxx---
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response  # <---xxx--- удаление пользователя
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.models import User
from users.permissions import IsAdminOrOwner
from users.serializers import (
    ChangePhoneSerializer,
    UserESAProfileSerializer,
    UserFullSerializer,
    UserNewMsgsSerializer,
    UserPersonalAccountSerializer,
    UserSelfProfileSerializer,
)
from users.utils import delete_expired_tokens, update_token_field

# from django.contrib.auth import authenticate


@extend_schema(tags=['auth (token)'])
class CookieTokenObtainPairView(TokenObtainPairView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response = update_token_field(request, response)
        if not settings.DEBUG:  # для прода
            del response.data['refresh']  # refresh токен передается в куки
        return response


@extend_schema(tags=['auth (token)'])
class CookieTokenRefreshView(TokenRefreshView):
    """Обновление токенов через refresh cookie."""

    def post(self, request, *args, **kwargs):
        old_refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['REFRESH_COOKIE'])
        if not old_refresh_token:
            return Response(
                {'detail': 'Refresh token not found'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        data = request.data.copy()
        data['refresh'] = old_refresh_token
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        response = update_token_field(request, response)
        if 'refresh' in response.data and not settings.DEBUG:
            # refresh токен передается в куки
            del response.data['refresh']
        delete_expired_tokens()  # удаляем истекшие хэши токенов из базы данных
        return response


@extend_schema(tags=['auth (logout)'])
class LogoutView(APIView):
    """
    Выход пользователя из системы.
    Отзывает refresh-токен, делая его недействительным.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Создаем объект RefreshToken и добавляем в черный список
        token = RefreshToken(refresh_token)
        token.blacklist()  # Токен становится недействительным
        response = Response(
            {'detail': 'Successfully logged out.'}, status=status.HTTP_205_RESET_CONTENT
        )
        response.delete_cookie(
            'refresh_token', path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
        )
        return response


@extend_schema_view(
    create=extend_schema(summary='Создание "своего" пользователя'),
    list=extend_schema(
        summary='Просмотр списка пользователей (доступен только админу)'
    ),
)
class UserDevViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
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

    # добавлено, чтобы нельзя было создавать удаленного пользователя
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_deleted', False):
            raise ValidationError("Нельзя создать пользователя с 'is_deleted' = True.")
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@extend_schema(
    summary='Удаление пользователя по ID',
    description='Должны удалиться все его объявления<ul>'
    '<li>Надо проверить, что ему нельзя отправить сообщения'
    '<li>Надо проверить, что его объявления удаляются!'
    '<li>Если пользователь пытается удалить несуществующего пользователя, '
    "в любом случае ошибка 'нет прав'",
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'detail': {
                        'type': 'string',
                        'example': 'Пользователь 69 - username успешно удален.',
                    }
                },
            },
            description='Пользователь успешно удален',
        )
    },
)
class UserSoftDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    serializer_class = UserFullSerializer

    def get_queryset(self):
        return User.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        try:
            obj = queryset.get(id=self.kwargs['id'])
        except User.DoesNotExist as err:
            if self.request.user.is_staff or self.request.user.is_superuser:
                raise NotFound('Пользователь не найден.') from err
            raise PermissionDenied(
                'У вас нет прав на удаление этого пользователя.'
            ) from err

        if obj != self.request.user and not (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            raise PermissionDenied('У вас нет прав на удаление этого пользователя.')
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the object for deletion
        username = instance.username  # Get the username *before* deleting
        instance.soft_delete()  # "Delete" the user
        return Response(
            {'detail': f'Пользователь {instance.id} - {username} удален'},
            status=status.HTTP_200_OK,
        )  # Return the success message


@extend_schema_view(
    put=extend_schema(
        request=UserSelfProfileSerializer,
        responses=UserSelfProfileSerializer,
        summary='Изменение профиля пользователя',
    ),
    patch=extend_schema(
        request=UserSelfProfileSerializer,
        responses=UserSelfProfileSerializer,
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
    get=extend_schema(summary='Просмотр краткой информации пользователя (в ЛК)'),
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
    get=extend_schema(summary='Наличие новых сообщений или уведомлений'),
)
class UserNewMsgsRetrieveAPIView(generics.RetrieveAPIView):
    """Получение информации о наличии новых сообщений или уведомлений.
    Используется в шапке."""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserNewMsgsSerializer

    def get_object(self):
        return self.request.user


# ========== СМЕНА НОМЕРА ТЕЛЕФОНА ==========
@extend_schema(
    tags=['users'],
    summary='Смена номера телефона',
    description='Позволяет авторизованному пользователю сменить номер телефона.',
    request=ChangePhoneSerializer,
    responses={
        200: OpenApiResponse(description='Номер телефона успешно изменён'),
        400: OpenApiResponse(description='Ошибка валидации или номер уже занят'),
        401: OpenApiResponse(description='Пользователь не авторизован'),
    },
)
class ChangePhoneAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePhoneSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Номер телефона успешно изменён.'}, status=status.HTTP_200_OK
        )
