import re

import django_filters
from django.contrib.postgres.search import TrigramSimilarity
from django.db import connection
from django.db.models import F, Q

from config import constants
from .models import Realty


class RealtyFilter(django_filters.FilterSet):
    """Custom filterset for Realty model."""

    bathroom_type = django_filters.BaseInFilter(
        field_name='common_characteristics__bathroom__type',
        lookup_expr='in',
        help_text='Тип санузла (Раздельный или Совмещенный). (Значения вводить с учетом регистра! '
                  'Можно ввести несколько значений, через запятую без пробелов '
                  'или добавить значение в новый строковый элемент.)'
    )
    trade_type = django_filters.CharFilter(
        method='filter_trade_type',
        label='Тип сделки. (Аренда или Продажа)'
    )
    realty_type = django_filters.CharFilter(
        field_name='realty_type__type', lookup_expr='iexact',
        label='Тип недвижимости. (Квартира или Апартаменты)'
    )
    room_count = django_filters.BaseInFilter(
        field_name='about_apartment__number_of_rooms__number_of_rooms',
        lookup_expr='in',
        help_text='Кол-во комнат. (Значения вводить с учетом регистра! '
                  'Можно ввести несколько значений, через запятую без пробелов '
                  'или добавить значение в новый строковый элемент.)'
    )
    price_min = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte',
        label='Минимальная цена'
    )
    price_max = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte',
        label='Максимальная цена'
    )
    address_metro = django_filters.CharFilter(
        field_name='address__metro__name',
        lookup_expr='icontains',
        label='Метро'
    )
    address_street = django_filters.CharFilter(
        method='filter_address',
        lookup_expr='icontains',
        label='Улица или метро'
    )
    # address_street = django_filters.BaseInFilter(
    #    method='filter_address',
    #    label='Улица или метро',
    #    help_text='Можно ввести несколько значений, через запятую без пробелов '
    #              'или добавить значение в новый строковый элемент.'
    # )
    address_house_number = django_filters.CharFilter(
        field_name='address__house_number',
        lookup_expr='icontains',
        label='Номер дома'
    )
    area_min = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='gte',
        label='Общая площадь от'
    )
    area_max = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='lte',
        label='Общая площадь до'
    )
    floor_min = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='gte',
        label='Этаж от'
    )
    floor_max = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='lte',
        label='Этаж до'
    )
    not_first_floor = django_filters.BooleanFilter(
        method='filter_not_first_floor',
        label='Не первый этаж'
    )
    not_last_floor = django_filters.BooleanFilter(
        method='filter_not_last_floor',
        label='Не последний этаж'
    )
    has_balcony = django_filters.BooleanFilter(
        field_name='about_apartment__balcony',
        label='Балкон'
    )
    has_loggia = django_filters.BooleanFilter(
        field_name='about_apartment__loggia',
        label='Лоджия'
    )
    repair_type = django_filters.BaseInFilter(
        field_name='common_characteristics__repair_type__type',
        lookup_expr='in',
        help_text='Тип ремонта. (Значения вводить с учетом регистра! '
                  'Можно ввести несколько значений, через запятую без пробелов '
                  'или добавить значение в новый строковый элемент.)'
    )
    about_building = django_filters.BaseInFilter(
        field_name='about_building__type__type',
        lookup_expr='in',
        help_text='Тип дома. (Значения вводить с учетом регистра! '
                  'Можно ввести несколько значений, через запятую без пробелов '
                  'или добавить значение в новый строковый элемент.)'
    )
    has_furniture = django_filters.BooleanFilter(
        field_name='common_characteristics__furniture',
        label='Мебель'
    )
    has_refrigerator = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__fridge',
        label='Холодильник'
    )
    has_air_conditioning = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__conditioner',
        label='Кондиционер'
    )
    has_garbage_chute = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__garbage_chute',
        label='Мусоропровод'
    )
    has_tv = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__tv',
        label='Телевизор'
    )
    has_dishwasher = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__dishwasher',
        label='Посудомоечная машина'
    )
    has_washing_machine = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__washing_machine',
        label='Стиральная машина'
    )
    has_internet = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__internet',
        label='Интернет'
    )
    kids_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__kids_allowed',
        label='Можно с детьми'
    )
    animals_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__animals_allowed',
        label='Можно с животными'
    )
    no_deposit = django_filters.BooleanFilter(
        method='filter_no_deposit',
        label='Без залога'
    )
    no_commission = django_filters.BooleanFilter(
        method='filter_no_commission',
        label='Без комиссии'
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
        help_text='true - коммерческая, false - жилая'
    )

    commercial_type = django_filters.CharFilter(
        field_name='commercial_type',
        lookup_expr='exact',
        label='Тип коммерческой недвижимости',
        help_text='office, retail, warehouse, free_use, industrial'
    )

    class Meta:
        model = Realty
        fields = []

    def __init__(self, *args, **kwargs):  # <-- YYY --- Добавлено для фильтрации по is_deleted и владельцу
        super().__init__(*args, **kwargs)
        # По умолчанию показывать только не удаленные объявления
        self.queryset = self.queryset.filter(is_deleted=False,
                                             owner__is_deleted=False)

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
                Q(rent_profile__lease_payments__deposit__isnull=True) |
                Q(rent_profile__lease_payments__deposit=0)
            )
        return queryset

    def filter_no_commission(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(commission__isnull=True) | Q(commission=0)
            )
        return queryset

    def filter_address(self, queryset, name, value):
        ABBREVIATIONS = [
            r'\b[Уу]л(?:\.|-ца)?\.?\b',  # улица
            r'\b[Пп]р(?:\.|-кт)?\.?\b',  # проспект
            r'\b[Пп]ер\.?\b',  # переулок
            r'\b[Пп]л\.?\b',  # площадь
            r'\b[Шш](?:\.)?\.?\b',  # шоссе
            r'\b[Мм]кр(?:\.)?\.?\b',  # микрорайон
            r'\b[Нн]аб(?:\.)?\.?\b',  # набережная
            r'\b[Пп]р-д(?:\.)?\.?\b',  # проезд
            r'\b[Кк]в(?:\.)?\.?\b',  # квартал
            r'\b[Бб]-р(?:\.)?\.?\b',  # бульвар
            r'\b[Лл]ин(?:\.)?\.?\b',  # линия
            r'\b[Тт]уп(?:\.)?\.?\b',  # тупик
            r'\b[Аа]л(?:\.)?\.?\b',  # аллея
            r'\b[Вв]ъезд\b',  # въезд
            r'\b[Дд]ор(?:\.)?\.?\b',  # дорога
            r'\b[Пп]ос(?:\.)?\.?\b',  # поселок
            r'\b[Дд]ер(?:\.)?\.?\b',  # деревня
            r'\b[Сс]т(?:\.)?\.?\b',  # станция
            r'\b[Кк]м(?:\.)?\.?\b',  # километр
            r'\b[Уу]лица\b',
            r'\b[Пп]роспект\b',
            r'\b[Пп]ереулок\b',
            r'\b[Пп]лощадь\b',
            r'\b[Шш]оссе\b',
            r'\b[Мм]икрорайон\b',
            r'\b[Нн]абережная\b',
            r'\b[Пп]роезд\b',
            r'\b[Кк]вартал\b',
            r'\b[Бб]ульвар\b',
            r'\b[Лл]иния\b',
            r'\b[Тт]упик\b',
            r'\b[Аа]ллея\b',
            r'\b[Дд]орога\b',
            r'\b[Пп]оселок\b',
            r'\b[Дд]еревня\b',
            r'\b[Сс]танция\b',
            r'\b[А-Яа-я]{1,4}[.-][а-я]{0,3}\.?\b'
        ]
        if connection.vendor == 'postgresql':
            return queryset.annotate(
                street_similarity=TrigramSimilarity(
                    'address__street__name', value
                ),
                metro_similarity=TrigramSimilarity(
                    'address__metro__name', value
                )
            ).filter(
                Q(street_similarity__gt=0.25) |
                Q(metro_similarity__gt=0.25)
            )

        elif connection.vendor == 'sqlite':
            search_terms = [
                term.strip() for term in value.split(',') if term.strip()
            ]
            if not search_terms:
                return queryset
            query = Q()
            element_index = 0
            for term in search_terms:
                parts = term.split(' ')
                if len(parts) > 1:
                    for element in parts:
                        for pattern in ABBREVIATIONS:
                            if re.search(
                                    pattern,
                                    element,
                                    re.IGNORECASE
                            ):
                                element_index = parts.index(element)
                    parts.pop(element_index)
                    term = parts[0]
                term = term.capitalize()
                term_query = Q()
                term_query |= Q(address__street__name__icontains=term)
                term_query |= Q(address__metro__name__icontains=term)
                query |= term_query
            return queryset.filter(query).distinct()
        else:
            return queryset
        # if value:
        # Create a Q object for each value
        #    q_objects = Q()
        #    for v in value:
        # Split the search value into words
        #        words = v.strip().split()
        #        if not words:
        #            continue

        # For each value, create a condition where ALL words must be present
        # This allows searching for multi-word addresses like "Ленинский проспект"
        # All words must be in the same field (either all in street name or all in metro name)
        #        street_q = Q()
        #        metro_q = Q()

        #        for word in words:
        # Capitalize first letter, lowercase the rest
        #            word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
        # Each word must be present in street name
        #            if street_q:
        #                street_q &= Q(address__street__name__icontains=word)
        #            else:
        #                street_q = Q(address__street__name__icontains=word)
        # Each word must be present in metro name
        #            if metro_q:
        #                metro_q &= Q(address__metro__name__icontains=word)
        #            else:
        #                metro_q = Q(address__metro__name__icontains=word)

        # Either all words in street OR all words in metro
        #        value_q = street_q | metro_q

        # Different values in the list are combined with OR
        #        q_objects |= value_q
        #    return queryset.filter(q_objects)
        # return queryset
