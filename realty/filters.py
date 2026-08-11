import django_filters
from django.db.models import F, Q
from rest_framework.exceptions import ValidationError

from config import constants

from .models import Realty

TRADE_TYPE_SALE_VALUES = frozenset({'sale', constants.SALE_TRADE_TYPE.lower()})
TRADE_TYPE_RENT_VALUES = frozenset({'rent', constants.RENT_TRADE_TYPE.lower()})

STREET_TYPE_SYNONYMS = (
    ('проспект', 'пр-кт', 'пр-т', 'просп', 'пр'),
    ('улица', 'ул.', 'ул-ца', 'ул'),
    ('шоссе', 'ш.', 'ш'),
    ('переулок', 'пер.', 'пер'),
    ('площадь', 'пл.', 'пл'),
    ('бульвар', 'б-р', 'бул.', 'бул'),
    ('набережная', 'наб.', 'наб'),
    ('проезд', 'пр-д'),
    ('микрорайон', 'мкр.', 'мкр'),
    ('квартал', 'кв-л', 'кв.', 'кв'),
    ('аллея', 'ал.', 'ал'),
    ('тупик', 'туп.', 'туп'),
    ('линия', 'лин.', 'лин'),
    ('дорога', 'дор.', 'дор'),
    ('поселок', 'посёлок', 'пос.', 'пос'),
    ('деревня', 'дер.', 'дер'),
    ('станция', 'ст.', 'ст'),
)

STREET_TYPE_SEARCHABLE = {
    form
    for group in STREET_TYPE_SYNONYMS
    for form in group
    if len(form) > 4 or not form.isalpha()
}

STREET_TYPE_LOOKUP = {
    form.rstrip('.'): tuple(f for f in group if f in STREET_TYPE_SEARCHABLE)
    for group in STREET_TYPE_SYNONYMS
    for form in group
}


class PriceRangeFilterSet(django_filters.FilterSet):
    """Базовый filterset с диапазоном цены. Переиспользуется поиском и каталогом."""

    price_min = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte', label='Минимальная цена'
    )
    price_max = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte', label='Максимальная цена'
    )


class RealtyFilter(PriceRangeFilterSet):
    """Custom filterset for Realty model."""

    bathroom_type = django_filters.BaseInFilter(
        field_name='common_characteristics__bathroom__type',
        lookup_expr='in',
        help_text='Тип санузла (Раздельный или Совмещенный). (Значения вводить с учетом регистра! '
        'Можно ввести несколько значений, через запятую без пробелов '
        'или добавить значение в новый строковый элемент.)',
    )
    trade_type = django_filters.CharFilter(
        method='filter_trade_type', label='Тип сделки. (Аренда или Продажа)'
    )
    realty_type = django_filters.CharFilter(
        field_name='realty_type__type',
        lookup_expr='iexact',
        label='Тип недвижимости. (Квартира или Апартаменты)',
    )
    room_count = django_filters.BaseInFilter(
        field_name='about_apartment__number_of_rooms__number_of_rooms',
        lookup_expr='in',
        help_text='Кол-во комнат. (Значения вводить с учетом регистра! '
        'Можно ввести несколько значений, через запятую без пробелов '
        'или добавить значение в новый строковый элемент.)',
    )
    address_metro = django_filters.CharFilter(
        field_name='address__metro__name', lookup_expr='icontains', label='Метро'
    )
    address_street = django_filters.CharFilter(
        method='filter_address',
        label='Улица или метро',
        help_text='Поиск по названию улицы или станции метро (частичное совпадение, '
        'без учета регистра). Понимает сокращения: пр-кт, ул., ш. и т.п.',
    )
    # address_street = django_filters.BaseInFilter(
    #    method='filter_address',
    #    label='Улица или метро',
    #    help_text='Можно ввести несколько значений, через запятую без пробелов '
    #              'или добавить значение в новый строковый элемент.'
    # )
    address_house_number = django_filters.CharFilter(
        field_name='address__house_number', lookup_expr='icontains', label='Номер дома'
    )
    area_min = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='gte', label='Общая площадь от'
    )
    area_max = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='lte', label='Общая площадь до'
    )
    floor_min = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='gte', label='Этаж от'
    )
    floor_max = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='lte', label='Этаж до'
    )
    not_first_floor = django_filters.BooleanFilter(
        method='filter_not_first_floor', label='Не первый этаж'
    )
    not_last_floor = django_filters.BooleanFilter(
        method='filter_not_last_floor', label='Не последний этаж'
    )
    has_balcony = django_filters.BooleanFilter(
        field_name='about_apartment__balcony', label='Балкон'
    )
    has_loggia = django_filters.BooleanFilter(
        field_name='about_apartment__loggia', label='Лоджия'
    )
    repair_type = django_filters.BaseInFilter(
        field_name='common_characteristics__repair_type__type',
        lookup_expr='in',
        help_text='Тип ремонта. (Значения вводить с учетом регистра! '
        'Можно ввести несколько значений, через запятую без пробелов '
        'или добавить значение в новый строковый элемент.)',
    )
    about_building = django_filters.BaseInFilter(
        field_name='about_building__type__type',
        lookup_expr='in',
        help_text='Тип дома. (Значения вводить с учетом регистра! '
        'Можно ввести несколько значений, через запятую без пробелов '
        'или добавить значение в новый строковый элемент.)',
    )
    has_furniture = django_filters.BooleanFilter(
        field_name='common_characteristics__furniture', label='Мебель'
    )
    has_refrigerator = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__fridge', label='Холодильник'
    )
    has_air_conditioning = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__conditioner', label='Кондиционер'
    )
    has_garbage_chute = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__garbage_chute', label='Мусоропровод'
    )
    has_tv = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__tv', label='Телевизор'
    )
    has_dishwasher = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__dishwasher',
        label='Посудомоечная машина',
    )
    has_washing_machine = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__washing_machine',
        label='Стиральная машина',
    )
    has_internet = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__internet', label='Интернет'
    )
    kids_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__kids_allowed', label='Можно с детьми'
    )
    animals_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__animals_allowed',
        label='Можно с животными',
    )
    no_deposit = django_filters.BooleanFilter(
        method='filter_no_deposit', label='Без залога'
    )
    no_commission = django_filters.BooleanFilter(
        method='filter_no_commission', label='Без комиссии'
    )
    ordering = django_filters.OrderingFilter(
        fields={
            'published_at': 'published_at',
            'price': 'price',
        },
        field_labels={
            'published_at': 'Дата публикации',
            'price': 'Цена',
        },
        label='Сортировка',
        help_text='Выберите порядок сортировки: '
        '"-published_at" - сначала новые, '
        '"price" - по возрастанию цены, '
        '"-price" - по убыванию цены.',
    )

    is_commercial = django_filters.BooleanFilter(
        field_name='realty_type__is_commercial',
        label='Тип недвижимости (жилая/коммерческая)',
        help_text='true - коммерческая, false - жилая',
    )

    commercial_type = django_filters.CharFilter(
        field_name='commercial_type',
        lookup_expr='exact',
        label='Тип коммерческой недвижимости',
        help_text='office, retail, warehouse, free_use, industrial',
    )

    class Meta:
        model = Realty
        fields = []

    def __init__(
        self, *args, **kwargs
    ):  # <-- YYY --- Добавлено для фильтрации по is_deleted и владельцу
        super().__init__(*args, **kwargs)
        # По умолчанию показывать только не удаленные объявления
        self.queryset = self.queryset.filter(is_deleted=False, owner__is_deleted=False)

    def filter_trade_type(self, queryset, name, value):
        if value.lower() == constants.SALE_TRADE_TYPE.lower():
            return queryset.filter(sale_profile__isnull=False)
        elif value.lower() == constants.RENT_TRADE_TYPE.lower():
            return queryset.filter(rent_profile__isnull=False)
        return queryset

    def filter_not_first_floor(self, queryset, name, value):
        if value:
            return queryset.filter(about_apartment__floor__gt=1)
        return queryset

    def filter_not_last_floor(self, queryset, name, value):
        if value:
            return queryset.exclude(
                about_apartment__floor=F('about_apartment__floors_number')
            )
        return queryset

    def filter_no_deposit(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(rent_profile__lease_payments__deposit__isnull=True)
                | Q(rent_profile__lease_payments__deposit=0)
            )
        return queryset

    def filter_no_commission(self, queryset, name, value):
        if value:
            return queryset.filter(Q(commission__isnull=True) | Q(commission=0))
        return queryset

    @staticmethod
    def _address_word_q(field, word):
        """Условие для одного слова запроса.
        Тип улицы («пр-кт») ищется по всем своим написаниям сразу."""
        variants = STREET_TYPE_LOOKUP.get(word.lower().rstrip('.'))
        if not variants:
            return Q(**{f'{field}__icontains': word})

        query = Q()
        for variant in variants:
            query |= Q(**{f'{field}__icontains': variant})
        return query

    def filter_address(self, queryset, name, value):
        """Поиск по названию улицы или станции метро."""
        words = value.split() if value else []
        if not words:
            return queryset

        street_q = Q()
        metro_q = Q()
        for word in words:
            street_q &= self._address_word_q('address__street__name', word)
            metro_q &= self._address_word_q('address__metro__name', word)

        return queryset.filter(street_q | metro_q)


class CatalogPriceFilter(PriceRangeFilterSet):
    class Meta:
        model = Realty
        fields = []


class LatestRealtyFilter(RealtyFilter):
    """RealtyFilter со строгой валидацией trade_type для эндпоинта /api/realty/latest/."""

    def filter_trade_type(self, queryset, name, value):
        normalized = value.strip().lower()
        if normalized in TRADE_TYPE_SALE_VALUES:
            return queryset.filter(sale_profile__isnull=False)
        if normalized in TRADE_TYPE_RENT_VALUES:
            return queryset.filter(rent_profile__isnull=False)
        raise ValidationError(
            {
                name: (
                    f"Недопустимое значение '{value}'. "
                    f'Допустимые значения: sale, rent.'
                )
            }
        )
