import django_filters
from django.db.models import Q
from .models import Metro
import re

class MetroFilter(django_filters.FilterSet):
    """Custom filterset for Metro model."""
    
    station_name = django_filters.CharFilter(
        method='filter_station_name',
        label='Название станции метро',
        help_text='Поиск по названию станции (частичное совпадение, без учета регистра)'
    )
    
    line_name = django_filters.CharFilter(
        method='filter_line_name',
        label='Название линии метро',
        help_text='Поиск по названию линии метро (частичное совпадение, без учета регистра)'
    )
    
    def _clean_station_name(self, value):
        """Remove 'станция' word from search value."""
        if not value:
            return value

        KEYWORDS_TO_REMOVE = [
            r'\bстанция метро\b',
            r'\bметро\b',
            r'\bстанция\b',
        ]

        for word in KEYWORDS_TO_REMOVE:
            value = re.sub(word, '', value, flags=re.IGNORECASE)

        return value.strip()
    
    def _clean_line_name(self, value):
        """Remove 'линия' word from search value."""
        if not value:
            return value
        # Remove 'линия' word case-insensitively
        return re.sub(r'\s*линия\s*', ' ', value, flags=re.IGNORECASE).strip()
    
    def filter_station_name(self, queryset, name, value):
        if value:
            # Clean the search value
            cleaned_value = self._clean_station_name(value)
            return queryset.filter(
                Q(name__icontains=cleaned_value) | 
                Q(name_full__icontains=cleaned_value)
            )
        return queryset
    
    def filter_line_name(self, queryset, name, value):
        if value:
            # Clean the search value
            cleaned_value = self._clean_line_name(value)
            return queryset.filter(
                Q(line__name__icontains=cleaned_value) | 
                Q(line__name_full__icontains=cleaned_value)
            )
        return queryset
    
    class Meta:
        model = Metro
        fields = ['station_name', 'line_name'] 