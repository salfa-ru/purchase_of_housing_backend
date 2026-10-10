from django.db import transaction
from drf_spectacular.helpers import forced_singular_serializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config import constants
from realty.models import Realty
from users.models import User

from .models import Comparison
from .serializers import ComparisonListSerializer, ComparisonSerializer

LIMIT_REACHED = (
    f'В сравнении может быть не больше {constants.COMPARISON_MAX} объявлений. '
    'Удалите одно из них, чтобы добавить новое.'
)
ALREADY_ADDED = 'Объявление уже добавлено в сравнение.'
NOT_AVAILABLE = 'Добавить в сравнение можно только опубликованное объявление.'
REALTY_NOT_FOUND = 'Объявление не найдено.'
NOT_IN_COMPARISON = 'Этого объявления нет в сравнении.'


@extend_schema_view(
    get=extend_schema(
        tags=['Сравнение'],
        summary='Список сравнения',
        description='Объявления в сравнении текущего пользователя в порядке '
        'добавления, с полными характеристиками для таблицы. Удалённые и '
        'архивные объявления остаются в списке с is_available=false и '
        'занимают место, пока пользователь их не уберёт. У удалённого '
        'объявления realty = null, убрать его можно по realty_id.',
        responses={200: forced_singular_serializer(ComparisonListSerializer)},
    ),
    post=extend_schema(
        tags=['Сравнение'],
        summary='Добавление объявления в сравнение',
        description='Принимает realty_id. Добавить можно только опубликованное '
        f'объявление и не больше {constants.COMPARISON_MAX} штук. '
        'Повтор, превышение лимита или неопубликованное объявление — 400, '
        'несуществующее или удалённое — 404.',
        request=ComparisonSerializer,
        responses={201: ComparisonSerializer},
    ),
)
class ComparisonListCreateView(generics.ListCreateAPIView):
    """Список сравнения текущего пользователя и добавление в него объявления."""

    permission_classes = [IsAuthenticated]
    serializer_class = ComparisonSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Comparison.objects.filter(user=self.request.user)
            .select_related(
                'realty__owner', 'realty__realty_status', 'realty__realty_type'
            )
            .prefetch_related('realty__realty_photos')
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(
            {
                'count': len(serializer.data),
                'max_count': constants.COMPARISON_MAX,
                'results': serializer.data,
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        realty = (
            Realty.objects.filter(
                id=serializer.validated_data['realty_id'],
                is_deleted=False,
                owner__is_deleted=False,
            )
            .select_related('realty_status')
            .first()
        )
        if realty is None:
            raise NotFound({'detail': REALTY_NOT_FOUND})
        if realty.realty_status_id != constants.STATUS_ACTIVE_ID:
            raise ValidationError({'detail': NOT_AVAILABLE})

        with transaction.atomic():
            User.objects.select_for_update().filter(pk=request.user.pk).first()
            comparisons = Comparison.objects.filter(user=request.user)

            if comparisons.filter(realty=realty).exists():
                raise ValidationError({'detail': ALREADY_ADDED})
            if comparisons.count() >= constants.COMPARISON_MAX:
                raise ValidationError({'detail': LIMIT_REACHED})

            comparison = Comparison.objects.create(user=request.user, realty=realty)

        return Response(
            self.get_serializer(comparison).data, status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=['Сравнение'],
    summary='Удаление объявления из сравнения',
    description='Убирает объявление из сравнения по его ID (ID объявления, '
    'а не записи сравнения). Возвращает 204 No Content.',
    responses={204: None},
)
class ComparisonDeleteView(generics.DestroyAPIView):
    """Убирает объявление из сравнения текущего пользователя."""

    permission_classes = [IsAuthenticated]
    lookup_field = 'realty_id'

    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user)

    def get_object(self):
        comparison = self.get_queryset().filter(realty_id=self.kwargs['realty_id'])
        instance = comparison.first()
        if instance is None:
            raise NotFound({'detail': NOT_IN_COMPARISON})
        return instance
