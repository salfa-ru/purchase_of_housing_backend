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

TRADE_TYPES = ('sale', 'rent')
TRADE_TYPE_FILTERS = {
    'sale': {'realty__sale_profile__isnull': False},
    'rent': {'realty__rent_profile__isnull': False},
}

LIMIT_REACHED = f'Можно сравнить не более {constants.COMPARISON_MAX} объявлений'
ALREADY_ADDED = 'Объявление уже добавлено в сравнение.'
NOT_AVAILABLE = 'Добавить в сравнение можно только опубликованное объявление.'
NO_TRADE_TYPE = (
    'У объявления не указано, продажа это или аренда, поэтому его не с чем сравнить.'
)
KIND_LABELS = {False: 'жилую', True: 'коммерческую'}
OTHER_KIND = (
    'В этом списке сравнивается {current} недвижимость. Чтобы сравнить '
    '{other}, сначала уберите объявления из списка.'
)
REALTY_NOT_FOUND = 'Объявление не найдено.'
NOT_IN_COMPARISON = 'Этого объявления нет в сравнении.'


def list_is_commercial(comparisons):
    """Вид списка задаёт первое добавленное объявление: жилое или коммерческое.
    У пустого списка вида нет — None."""
    first = comparisons.select_related('realty__realty_type').first()
    if first is None:
        return None
    return first.realty.realty_type.is_commercial


@extend_schema_view(
    get=extend_schema(
        tags=['Сравнение'],
        summary='Списки сравнения',
        description='У пользователя два списка сравнения: продажа (sale) и '
        'аренда (rent). Объявление само попадает в список своего типа сделки, '
        'поэтому смешать продажу и аренду в одной таблице нельзя. Жилую и '
        'коммерческую недвижимость тоже нельзя: вид списка задаёт первое '
        'добавленное объявление, он приходит в is_commercial (null у пустого '
        'списка). В каждом '
        f'списке до {constants.COMPARISON_MAX} объявлений, в порядке '
        'добавления, с полными характеристиками для таблицы. Пустой список '
        'отдаётся с count = 0.\n\n'
        'Группы строк таблицы. Жильё: «Общие сведения» — price, trade_type, '
        'owner_type, address; «О квартире» — about_apartment; «О доме» — '
        'about_building. Коммерция: «Общие сведения» — то же; «О здании» — '
        'commercial_characteristics.building_type и entrance; «О помещении» — '
        'about_apartment.area, floor, floors_number и '
        'commercial_characteristics.ceiling_height, heating, finishing, '
        'has_furniture.\n\n'
        'Удалённые и архивные объявления остаются в списке с '
        'is_available=false и занимают место, пока пользователь их не уберёт. '
        'У удалённого объявления realty = null, убрать его можно по realty_id.',
        responses={200: forced_singular_serializer(ComparisonListSerializer)},
    ),
    post=extend_schema(
        tags=['Сравнение'],
        summary='Добавление объявления в сравнение',
        description='Принимает realty_id. Объявление попадает в список продажи '
        'или аренды по своему типу сделки (trade_type в ответе). Добавить можно '
        'только опубликованное объявление и не больше '
        f'{constants.COMPARISON_MAX} штук в один список: при попытке добавить '
        f'лишнее — 400 с текстом «{LIMIT_REACHED}». Коммерческое объявление в '
        'список с жилыми (и наоборот) — 400. Повтор или '
        'неопубликованное объявление — тоже 400, несуществующее или '
        'удалённое — 404.',
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
                'realty__owner',
                'realty__realty_status',
                'realty__realty_type',
                'realty__sale_profile',
                'realty__rent_profile',
            )
            .prefetch_related('realty__realty_photos')
        )

    def list(self, request, *args, **kwargs):
        data = {'max_count': constants.COMPARISON_MAX}
        for trade_type in TRADE_TYPES:
            queryset = self.get_queryset().filter(**TRADE_TYPE_FILTERS[trade_type])
            results = self.get_serializer(queryset, many=True).data
            data[trade_type] = {
                'count': len(results),
                'is_commercial': list_is_commercial(queryset),
                'results': results,
            }
        return Response(data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        realty = (
            Realty.objects.filter(
                id=serializer.validated_data['realty_id'],
                is_deleted=False,
                owner__is_deleted=False,
            )
            .select_related(
                'realty_status', 'realty_type', 'sale_profile', 'rent_profile'
            )
            .first()
        )
        if realty is None:
            raise NotFound({'detail': REALTY_NOT_FOUND})
        if realty.realty_status_id != constants.STATUS_ACTIVE_ID:
            raise ValidationError({'detail': NOT_AVAILABLE})
        if realty.trade_type not in TRADE_TYPES:
            raise ValidationError({'detail': NO_TRADE_TYPE})

        with transaction.atomic():
            User.objects.select_for_update().filter(pk=request.user.pk).first()
            comparisons = Comparison.objects.filter(user=request.user)

            if comparisons.filter(realty=realty).exists():
                raise ValidationError({'detail': ALREADY_ADDED})
            same_list = comparisons.filter(**TRADE_TYPE_FILTERS[realty.trade_type])
            current = list_is_commercial(same_list)
            if current is not None and current != realty.realty_type.is_commercial:
                raise ValidationError(
                    {
                        'detail': OTHER_KIND.format(
                            current=KIND_LABELS[current],
                            other=KIND_LABELS[not current],
                        )
                    }
                )
            if same_list.count() >= constants.COMPARISON_MAX:
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
