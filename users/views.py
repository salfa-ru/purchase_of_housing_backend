from django.http import JsonResponse
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework import permissions

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.response import Response  # <---xxx--- удаление пользователя
from rest_framework import serializers, status  # <---xxx--- удаление пользователя
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError  # <---xxx---
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework.permissions import IsAuthenticated

from django.conf import settings

from users.models import User
from users.permissions import IsAdminOrOwner
from users.serializers import (
    UserFullSerializer,
    UserSelfProfileSerializer,
    UserESAProfileSerializer,
    UserPersonalAccountSerializer,
    UserNewMsgsSerializer, ChangePhoneSerializer
)
from users.utils import delete_expired_tokens, update_token_field


# from django.contrib.auth import authenticate


class CookieTokenObtainPairView(TokenObtainPairView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # del response.data['access']
        response = update_token_field(request, response)
        del response.data['refresh']  # refresh токен передается в куки
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Обновление токенов через refresh cookie."""

    def post(self, request, *args, **kwargs):
        old_refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT['REFRESH_COOKIE']
        )
        if not old_refresh_token:
            return Response(
                {"detail": "Refresh token not found"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        request.data['refresh'] = old_refresh_token
        response = super().post(request, *args, **kwargs)
        response = update_token_field(request, response)
        #    del response.data['access']
        if 'refresh' in response.data:  # refresh токен передается в куки
            del response.data['refresh']
        delete_expired_tokens()  # удаляем истекшие хэши токенов из базы данных
        return response


# class CustomAuthToken(ObtainAuthToken):
#    """ Замена для обработки мягко-удаленных пользователей
#    Вообще, они при "удалении" еще и дезактивируются, так что
#    добавление кастомной функции не является необходимостью. """
#    def post(self, request, *args, **kwargs):
#        serializer = self.serializer_class(data=request.data,
#                                           context={'request': request})
#        try:
#           serializer.is_valid(raise_exception=True)
#        except serializers.ValidationError as e:
#          # Handle authentication failure here
#            # Attempt to authenticate the user to check the actual cause of the error
#            username = request.data.get('username')  # Or 'email', depending on your setup
#            password = request.data.get('password')
#            user = authenticate(username=username, password=password)
#           if user is None:
#                return Response({"detail": "Невозможно войти с предоставленными учетными данными."},
#                                status=status.HTTP_400_BAD_REQUEST)  # Bad Request
#            else:
#               # If user exists but other validations failed, reraise it
#                return Response(e.detail,
#                               status=status.HTTP_400_BAD_REQUEST)
#        user = serializer.validated_data['user']
#       # Check if user is deleted *here*
#        if user.is_deleted:
#            return Response({"detail": "Учетная запись пользователя удалена."},
#                            status=status.HTTP_400_BAD_REQUEST)  # Bad Request
#        token, created = Token.objects.get_or_create(user=user)
#        response = JsonResponse({
#            'user_id': user.pk,
#            'email': user.email
#        })
# Добавление токена в куки.
#        response.set_cookie(
#            key='auth_token',
#            value=token.key,
#            httponly=True,  # Запрет доступа из JavaScript
#            secure=True,    # Только по HTTPS (в продакшне)
#            samesite='Lax'  # Защита от CSRF (частично)
#        )
#        return response

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
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        response = Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT
        )
        response.delete_cookie(
            'refresh_token',
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
        )
        return response


@extend_schema_view(
    create=extend_schema(summary='Создание "своего" пользователя'),
    list=extend_schema(summary='Просмотр списка пользователей (доступен только админу)'),
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

    # добавлено, чтобы нельзя было создавать удаленного пользователя
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get('is_deleted', False):
            raise ValidationError("Нельзя создать пользователя с 'is_deleted' = True.")
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    summary="Удаление пользователя по ID",
    description="Должны удалиться все его объявления<ul>"
                "<li>Надо проверить, что ему нельзя отправить сообщения"
                "<li>Надо проверить, что его объявления удаляются!"
                "<li>Если пользователь пытается удалить несуществующего пользователя, "
                "в любом случае ошибка 'нет прав'",

    responses={200: OpenApiResponse(response={
        "type": "object",
        "properties": {
            "detail": {"type": "string", "example": "Пользователь 69 - username успешно удален."}
        }
    },
        description="Пользователь успешно удален")}
)
class UserSoftDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    serializer_class = UserFullSerializer

    def get_queryset(self):
        return User.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        try:
            obj = queryset.get(id=self.kwargs["id"])
        except User.DoesNotExist:
            if self.request.user.is_staff or self.request.user.is_superuser:
                raise NotFound("Пользователь не найден.")
            raise PermissionDenied("У вас нет прав на удаление этого пользователя.")

        if obj != self.request.user and not (self.request.user.is_staff or self.request.user.is_superuser):
            raise PermissionDenied("У вас нет прав на удаление этого пользователя.")
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the object for deletion
        username = instance.username  # Get the username *before* deleting
        instance.soft_delete()  # "Delete" the user
        return Response({"detail": f"Пользователь {instance.id} - {username} удален"},
                        status=status.HTTP_200_OK)  # Return the success message


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
    summary="Смена номера телефона",
    description="Позволяет авторизованному пользователю сменить номер телефона.",
    request=ChangePhoneSerializer,
    responses={
        200: OpenApiResponse(description="Номер телефона успешно изменён"),
        400: OpenApiResponse(description="Ошибка валидации или номер уже занят"),
        401: OpenApiResponse(description="Пользователь не авторизован"),
    }
)
class ChangePhoneAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePhoneSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Номер телефона успешно изменён."},
            status=status.HTTP_200_OK
        )
