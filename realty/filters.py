import django_filters
from django.db.models import F, Q
from django.utils.functional import lazy

from config import constants
from .models import Realty
from realty_values.models import BathroomType


def get_bathroom_type_choices():
    return [(bt.type, bt.type) for bt in BathroomType.objects.all()]


class RealtyFilter(django_filters.FilterSet):
    """Custom filterset for Realty model."""

    BATHROOM_TYPE_CHOICES = lazy(get_bathroom_type_choices, list)()

    bathroom_type = django_filters.MultipleChoiceFilter(
        choices=BATHROOM_TYPE_CHOICES,
        field_name='common_characteristics__bathroom__type',
        label='Тип санузла'
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
        field_name='address__street__name',
        lookup_expr='icontains',
        label='Улица'
    )
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
    # pub_date = django_filters.OrderingFilter(
    #     fields=('published_at',),
    # )
    # price_ordrering = django_filters.OrderingFilter(
    #     fields=('price',),
    # )
    ordering = django_filters.OrderingFilter(
        fields={
            'published_at': 'published_at',  # Сортировка по дате публикации
            'price': 'price',  # Сортировка по цене
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

    class Meta:
        model = Realty
        fields = []

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
