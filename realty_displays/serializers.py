from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers


class CounterViewsSerializer(serializers.Serializer):
    """Serializer for view counters."""

    # отдаст Nulls если записей вообще нет, но вообще можно было бы показывать нули (default=0)
    shown_in_search = serializers.IntegerField(default=None, allow_null=True)
    full_views_in_30_days = serializers.IntegerField(default=None, allow_null=True)
    full_views_today = serializers.IntegerField(default=None, allow_null=True)

    def to_representation(self, instance):
        representation = {}

        search_count_obj = instance.display_in_search.first()
        search_count = search_count_obj.count if search_count_obj else None
        representation['shown_in_search'] = search_count

        # из-за фильтра data_gte добавляется +день к поиску!
        # так что устанавливаю 29 а не 30
        last_30_days = timezone.now() - timedelta(days=29)

        views_30_days = instance.display_full_info.filter(
            date__gte=last_30_days
        ).aggregate(total=Sum('count'))['total']
        representation['full_views_in_30_days'] = (
            views_30_days if views_30_days is not None else None
        )

        today = timezone.now().date()
        views_today = instance.display_full_info.filter(date=today).aggregate(
            total=Sum('count')
        )['total']
        representation['full_views_today'] = (
            views_today if views_today is not None else None
        )

        return representation
