from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Favorite
from .serializers import FavoriteSerializer
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter


@extend_schema(
    summary='Получение списка избранного пользователя',
    description='Возвращает список объявлений в избранном с количеством непросмотренных. Поддерживает фильтрацию по trade_type, realty_type и ordering.',
    parameters=[
        OpenApiParameter(name='trade_type', description='sale или rent', required=False, type=str),
        OpenApiParameter(name='realty_type', description='apartment, apartments, commercial', required=False, type=str),
        OpenApiParameter(name='ordering', description='-added_at (сначала новые)', required=False, type=str),
    ]
)
class FavoriteListView(generics.ListAPIView):
    """
        Возвращает список избранных объявлений текущего пользователя.

        Поддерживает фильтрацию:
        - `trade_type` — тип сделки (sale/rent)
        - `realty_type` — тип недвижимости (apartment/apartments/commercial)
        - `ordering` — сортировка по дате добавления (added_at / -added_at)

        Ответ содержит:
        - `unviewed_count` — количество новых объявлений, добавленных после последнего посещения
        - `results` — список объектов избранного с полными данными объявлений

        Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Favorite.objects.filter(user=user)

        # Фильтрация
        trade_type = self.request.query_params.get('trade_type')
        realty_type = self.request.query_params.get('realty_type')
        ordering = self.request.query_params.get('ordering', 'added_at')

        if trade_type:
            queryset = queryset.filter(realty__trade_type=trade_type)
        if realty_type:
            queryset = queryset.filter(realty__realty_type__type=realty_type)

        return queryset.order_by(ordering)

    def list(self, request, *args, **kwargs):
        """
            Переопределяем, чтоб добавить unviewed_count в ответ.
        """

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Считаем количество непросмотренных
        unviewed_count = queryset.filter(is_viewed=False).count()

        # Возвращаем объект с двумя полями
        return Response({
            'unviewed_count': unviewed_count,
            'results': serializer.data
        })


@extend_schema(
    summary='Добавление объявления в избранное',
    description='Принимает realty_id и добавляет объявление в избранное текущего пользователя',
    request=FavoriteSerializer,
    responses={201: FavoriteSerializer}
)
class FavoriteCreateView(generics.CreateAPIView):
    """
        Добавляет объявление в избранное текущего пользователя.

        Ожидает JSON:
        {
            "realty_id": 123
        }

        Возвращает созданный объект избранного с вложенными данными объявления.

        Если объявление уже в избранном — возвращает ошибку 400.
        Доступно только авторизованным пользователям.
    """
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def post(self, request, *args, **kwargs):
        print("🔥 POST в FavoriteCreateView")  # 👈 временная строка
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary='Удаление объявления из избранного',
    description='Мгновенное удаление без подтверждения. Возвращает 204 No Content.',
    responses={204: None}
)
class FavoriteDeleteView(generics.DestroyAPIView):
    """
        Удаляет объявление из избранного по ID записи избранного.

        Удаление происходит мгновенно, без дополнительного подтверждения.
        Пользователь может удалять только свои записи.

        Возвращает статус 204 No Content при успешном удалении.
        Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]
    queryset = Favorite.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        # Пользователь может удалять только свое избранное
        return self.queryset.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary='Сброс счётчика непросмотренных',
    description='Помечает все объявления в избранном как просмотренные (is_viewed = True)',
    responses={200: None}
)
class FavoriteMarkViewedView(APIView):
    """
        Сбрасывает счётчик новых объявлений в избранном.

        Вызывается при заходе пользователя на страницу /favorites.
        Устанавливает флаг `is_viewed = True` для всех непросмотренных записей текущего пользователя.

        Возвращает:
        {
            "status": "viewed",
            "update_count": количество обновлённых записей
        }

        Доступно только авторизованным пользователям.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Обновляем все непросмотренные записи текущего пользователя
        updated = Favorite.objects.filter(
            user=request.user,
            is_viewed=False
        ).update(is_viewed=True)

        return Response({
            'status': 'viewed',
            'update_count': updated
        }, status=status.HTTP_204_NO_CONTENT)
