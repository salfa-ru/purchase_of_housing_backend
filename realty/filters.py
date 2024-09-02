import django_filters
from django.db.models import F, Q

from .models import Realty


class RealtyFilter(django_filters.FilterSet):
    trade_type = django_filters.CharFilter(
        method='filter_trade_type'
    )
    realty_type = django_filters.CharFilter(
        field_name='realty_type__type', lookup_expr='iexact'
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
        field_name='address__metro__name', lookup_expr='icontains'
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
        method='filter_not_first_floor'
    )
    not_last_floor = django_filters.BooleanFilter(
        method='filter_not_last_floor'
    )
    has_balcony = django_filters.BooleanFilter(
        field_name='about_apartment__balcony'
    )
    has_loggia = django_filters.BooleanFilter(
        field_name='about_apartment__loggia'
    )
    repair_type = django_filters.CharFilter(
        field_name='common_characteristics__repair_type__type',
        lookup_expr='in'
    )
    about_building = django_filters.CharFilter(
        field_name='about_building__type__type', lookup_expr='in'
    )

    has_furniture = django_filters.BooleanFilter(
        field_name='common_characteristics__furniture'
    )
    has_refrigerator = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__fridge'
    )
    has_air_conditioning = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__conditioner'
    )
    has_garbage_chute = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__garbage_chute'
    )
    has_tv = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__tv'
    )
    has_dishwasher = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__dishwasher'
    )
    has_washing_machine = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__washing_machine'
    )
    has_internet = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__internet'
    )
    kids_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__kids_allowed'
    )
    animals_allowed = django_filters.BooleanFilter(
        field_name='rent_profile__rental_features__animals_allowed'
    )
    no_deposit = django_filters.BooleanFilter(
        method='filter_no_deposit'
        )
    no_commission = django_filters.BooleanFilter(
        field_name='commission', lookup_expr='isnull', exclude=False
    )

    class Meta:
        model = Realty
        fields = []

    def filter_trade_type(self, queryset, name, value):
        if value == 'sale':
            return queryset.filter(sale_profile__isnull=False)
        elif value == 'rent':
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
