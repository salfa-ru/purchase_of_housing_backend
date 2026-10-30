import django_filters
from django.db.models import F, Q
from rest_framework.exceptions import ValidationError

from config import constants
from realty_specificities.models import CommercialCharacteristics

from .models import Realty, Rent

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

# Символы, из которых состоят слова в названиях. Всё остальное (пробел, точка,
# запятая, дефис, начало и конец строки) считается границей слова.
WORD_CHARS = '0-9A-Za-zА-Яа-яЁё'
REGEX_SPECIAL_CHARS = frozenset('\\^$.|?*+()[]{}')


def _regex_atom(char):
    """Один символ шаблона: буква — в обоих регистрах, спецсимвол — экранированным."""
    lower, upper = char.lower(), char.upper()
    if lower != upper:
        return f'[{lower}{upper}]'
    if char in REGEX_SPECIAL_CHARS:
        return f'\\{char}'
    return char


def _street_type_pattern(forms):
    """Шаблон «одно из написаний типа улицы, стоящее отдельным словом»."""
    alternatives = '|'.join(''.join(_regex_atom(c) for c in form) for form in forms)
    return f'(^|[^{WORD_CHARS}])({alternatives})([^{WORD_CHARS}]|$)'


def _normalize_street_type_forms(group):
    """Написания без завершающей точки и без повторов: «ул.» и «ул» — одно и то же."""
    forms = []
    for form in group:
        form = form.rstrip('.')
        if form not in forms:
            forms.append(form)
    return tuple(forms)


STREET_TYPE_PATTERNS = {
    form: _street_type_pattern(_normalize_street_type_forms(group))
    for group in STREET_TYPE_SYNONYMS
    for form in _normalize_street_type_forms(group)
}


AREA_PARAMS = ('lat_min', 'lat_max', 'lon_min', 'lon_max')
AREA_INCOMPLETE = (
    'Для выделенной области нужны все четыре границы: '
    'lat_min, lat_max, lon_min, lon_max.'
)
AREA_LAT_ORDER = 'lat_min не может быть больше lat_max.'
AREA_LON_ORDER = 'lon_min не может быть больше lon_max.'


UNKNOWN_CHOICE = 'Недопустимое значение «{value}». Допустимые значения: {allowed}.'


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Несколько значений через запятую: office,warehouse."""


def choices_filter(field_name, choices, label):
    """Множественный выбор из списка кодов; неизвестный код — 400."""
    codes = [code for code, _ in choices]
    choice_filter = CharInFilter(
        field_name=field_name,
        method='filter_choices',
        label=label,
        help_text=f'Можно несколько через запятую: {", ".join(codes)}',
    )
    choice_filter.codes = codes
    return choice_filter


class PriceRangeFilterSet(django_filters.FilterSet):
    """Базовый filterset с диапазоном цены. Переиспользуется поиском и каталогом."""

    price_min = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte', label='Минимальная цена'
    )
    price_max = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte', label='Максимальная цена'
    )


class RealtyFilter(PriceRangeFilterSet):
    """Фильтры для объявлений."""

    bathroom_type = django_filters.BaseInFilter(
        field_name='common_characteristics__bathroom__type',
        lookup_expr='in',
        help_text='Тип санузла (Раздельный или Совмещенный). (Значения вводить с учетом'
        ' '
        'регистра! '
        'Можно ввести несколько значений, через запятую без пробелов '
        'или добавить значение в новый строковый элемент.)',
    )
    trade_type = django_filters.CharFilter(
        method='filter_trade_type',
        label='Тип сделки: sale или rent (можно Продажа или Аренда)',
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
        'без учета регистра). Понимает сокращения: пр-кт, ул., ш. и т.п. '
        'Несколько адресов перечисляются через запятую.',
    )
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
        method='filter_has_furniture',
        label='Мебель',
        help_text='У жилой — из общих характеристик, у коммерческой — '
        'из характеристик помещения',
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
    lat_min = django_filters.NumberFilter(
        field_name='address__latitude',
        lookup_expr='gte',
        min_value=-90,
        max_value=90,
        label='Выделенная область: южная граница (широта)',
    )
    lat_max = django_filters.NumberFilter(
        field_name='address__latitude',
        lookup_expr='lte',
        min_value=-90,
        max_value=90,
        label='Выделенная область: северная граница (широта)',
    )
    lon_min = django_filters.NumberFilter(
        field_name='address__longitude',
        lookup_expr='gte',
        min_value=-180,
        max_value=180,
        label='Выделенная область: западная граница (долгота)',
    )
    lon_max = django_filters.NumberFilter(
        field_name='address__longitude',
        lookup_expr='lte',
        min_value=-180,
        max_value=180,
        label='Выделенная область: восточная граница (долгота)',
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
        help_text='true - коммерческая, false - жилая. Не передан — только жилая '
        '(ФТ-1.3.1), если не выбраны тип недвижимости или коммерческие фильтры',
    )

    commercial_type = choices_filter(
        'commercial_type',
        Realty.COMMERCIAL_TYPE_CHOICES,
        'Назначение коммерческой недвижимости. Не выбрано — все назначения',
    )
    building_type = choices_filter(
        'commercial_characteristics__building_type',
        CommercialCharacteristics.BUILDING_TYPE_CHOICES,
        'Тип здания (коммерческая)',
    )
    entrance = choices_filter(
        'commercial_characteristics__entrance',
        CommercialCharacteristics.ENTRANCE_CHOICES,
        'Вход (коммерческая)',
    )
    heating = choices_filter(
        'commercial_characteristics__heating',
        CommercialCharacteristics.HEATING_CHOICES,
        'Отопление (коммерческая)',
    )
    finishing = choices_filter(
        'commercial_characteristics__finishing',
        CommercialCharacteristics.FINISHING_CHOICES,
        'Отделка (коммерческая)',
    )
    lease_type = choices_filter(
        'rent_profile__lease_type',
        Rent.LEASE_TYPE_CHOICES,
        'Тип аренды (коммерческая)',
    )
    utilities_included = django_filters.BooleanFilter(
        field_name='rent_profile__utilities_included',
        label='Коммунальные платежи включены (коммерческая аренда)',
    )

    residential_by_default = True
    KIND_PARAMS = (
        'is_commercial',
        'realty_type',
        'commercial_type',
        'building_type',
        'entrance',
        'heating',
        'finishing',
        'lease_type',
        'utilities_included',
    )

    class Meta:
        model = Realty
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.filter(is_deleted=False, owner__is_deleted=False)

    def filter_queryset(self, queryset):
        self._validate_area(self.form.cleaned_data)
        if self.residential_by_default and self._kind_not_chosen():
            queryset = queryset.filter(realty_type__is_commercial=False)
        return super().filter_queryset(queryset)

    def _kind_not_chosen(self):
        """Пользователь не выбрал ни вид недвижимости, ни коммерческий фильтр."""
        return all(
            self.form.cleaned_data.get(param) in (None, '', [])
            for param in self.KIND_PARAMS
        )

    def filter_choices(self, queryset, name, value):
        """Значения из списка кодов; подходит объявление с любым из них.
        django-filter передаёт в name поле модели, а не имя фильтра."""
        param, choice_filter = next(
            (param, choice_filter)
            for param, choice_filter in self.filters.items()
            if choice_filter.field_name == name
        )
        codes = choice_filter.codes
        value = [code.strip() for code in value if code.strip()]
        unknown = [code for code in value if code not in codes]
        if unknown:
            raise ValidationError(
                {
                    param: UNKNOWN_CHOICE.format(
                        value=unknown[0], allowed=', '.join(codes)
                    )
                }
            )
        if not value:
            return queryset
        return queryset.filter(**{f'{name}__in': value})

    def filter_has_furniture(self, queryset, name, value):
        """Мебель у жилой и у коммерческой хранится в разных местах."""
        return queryset.filter(
            Q(
                realty_type__is_commercial=False,
                common_characteristics__furniture=value,
            )
            | Q(
                realty_type__is_commercial=True,
                commercial_characteristics__has_furniture=value,
            )
        )

    @staticmethod
    def _validate_area(data):
        """Область на карте задаётся только целиком: все четыре границы сразу,
        минимум не больше максимума. Граница включается в область."""
        given = [param for param in AREA_PARAMS if data.get(param) is not None]
        if not given:
            return
        if len(given) < len(AREA_PARAMS):
            raise ValidationError({'detail': AREA_INCOMPLETE})

        errors = {}
        if data['lat_min'] > data['lat_max']:
            errors['lat_min'] = AREA_LAT_ORDER
        if data['lon_min'] > data['lon_max']:
            errors['lon_min'] = AREA_LON_ORDER
        if errors:
            raise ValidationError(errors)

    def filter_trade_type(self, queryset, name, value):
        normalized = value.strip().lower()
        if normalized in TRADE_TYPE_SALE_VALUES:
            return queryset.filter(sale_profile__isnull=False)
        elif normalized in TRADE_TYPE_RENT_VALUES:
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
        Тип улицы («ул», «ул.», «улица») ищется по всем своим написаниям сразу и
        только как отдельное слово, иначе «ул» нашлось бы внутри «Тульская».
        Остальные слова ищутся как часть названия.
        """
        pattern = STREET_TYPE_PATTERNS.get(word.lower().rstrip('.'))
        if pattern:
            return Q(**{f'{field}__regex': pattern})
        return Q(**{f'{field}__icontains': word})

    @classmethod
    def _address_phrase_q(cls, phrase):
        """Условие для одной фразы: все её слова должны найтись в улице либо в метро."""
        words = phrase.split()
        if not words:
            return None

        street_q = Q()
        metro_q = Q()
        for word in words:
            street_q &= cls._address_word_q('address__street__name', word)
            metro_q &= cls._address_word_q('address__metro__name', word)

        return street_q | metro_q

    def filter_address(self, queryset, name, value):
        """Поиск по названию улицы или станции метро.
        Запятая разделяет независимые адреса: подходит объект, попавший
        хотя бы под один из них.
        """
        query = Q()
        found = False
        for phrase in (value or '').split(','):
            phrase_q = self._address_phrase_q(phrase)
            if phrase_q is not None:
                query |= phrase_q
                found = True

        if not found:
            return queryset
        return queryset.filter(query)


class CatalogPriceFilter(PriceRangeFilterSet):
    class Meta:
        model = Realty
        fields = []


class LatestRealtyFilter(RealtyFilter):
    """RealtyFilter со строгой проверкой trade_type для /api/realty/latest/."""

    residential_by_default = False

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
