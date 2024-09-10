import django_filters
from django.db.models import F, Q

from config import constants
from .models import Realty


class RealtyFilter(django_filters.FilterSet):
    """Custom filterset for Realty model."""
    trade_type = django_filters.CharFilter(
        method='filter_trade_type'
    )
    realty_type = django_filters.CharFilter(
        field_name='realty_type__type', lookup_expr='iexact',
        help_text='Тип недвижимости'
    )
    room_count = django_filters.NumberFilter(
        field_name='about_apartment__number_of_rooms'
    )
    price_min = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte'
    )
    price_max = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte'
    )
    address_metro = django_filters.CharFilter(
        field_name='address__metro__name',
        lookup_expr='icontains',
    )
    address_street = django_filters.CharFilter(
        field_name='address__street__name',
        lookup_expr='icontains',
    )
    address_house_number = django_filters.CharFilter(
        field_name='address__house_number',
        lookup_expr='icontains',
    )
    area_min = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='gte'
    )
    area_max = django_filters.NumberFilter(
        field_name='about_apartment__area', lookup_expr='lte'
    )
    floor_min = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='gte'
    )
    floor_max = django_filters.NumberFilter(
        field_name='about_apartment__floor', lookup_expr='lte'
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
        lookup_expr='in'
    )
    about_building = django_filters.BaseInFilter(
        field_name='about_building__type__type',
        lookup_expr='in'
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
    separate_bathroom = django_filters.BooleanFilter(
        method='filter_separate_bathroom',
        label='Раздельный санузел'
    )
    combined_bathroom = django_filters.BooleanFilter(
        method='filter_combined_bathroom',
        label='Совмещенный санузел'
    )
    pub_date = django_filters.OrderingFilter(
        fields=('published_at',),
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

    def filter_separate_bathroom(self, queryset, name, value):
        if value:
            return queryset.filter(
                common_characteristics__bathroom__type=constants
                .SEPARATE_BATHROOM
            )
        return queryset

    def filter_combined_bathroom(self, queryset, name, value):
        if value:
            return queryset.filter(
                common_characteristics__bathroom__type=constants
                .COMBINED_BATHROOM
            )
        return queryset
